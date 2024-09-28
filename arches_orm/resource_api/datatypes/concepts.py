from __future__ import annotations

from collections import UserDict
from enum import Enum
from functools import partial
from lxml import etree as ET
import json
from urllib.parse import urlparse, urlunparse
from uuid import UUID
from pathlib import Path
from dataclasses import dataclass
from typing import TypedDict
import httpx
try:
    from typing import NotRequired
except ImportError: # 3.9
    from typing_extensions import NotRequired

from rdflib import Graph, Literal, Namespace, RDF
from rdflib.namespace import SKOS, DCTERMS
from arches_orm.collection import make_collection, CollectionEnum
from arches_orm.utils import consistent_uuid as cuuid
from arches_orm.adapter import get_adapter
from arches_orm.view_models.concepts import EmptyConceptValueViewModel, ConceptValueViewModel, ConceptListValueViewModel
from arches_orm.pseudo_node.datatypes._register import Tile, Node
from ._register import REGISTER, DEFAULT_LANGUAGE

_COLLECTIONS: dict[UUID, type[Enum]] = {}

@dataclass
class StaticValue:
    """Parallel of the Arches Value model."""

    id: UUID
    value: str
    language: str
    concept_id: UUID | None

    @classmethod
    def from_concept(cls, value_id: str | UUID) -> "StaticValue":
        value_id = UUID(value_id) if isinstance(value_id, str) else value_id
        value: "StaticValue"
        try:
            concept = next(concept for concept in _CONCEPTS.values() if hasattr(concept, "values") and value_id in concept.values)
            value = concept.values[value_id]
        except StopIteration:
            try:
                concept = next(concept for concept in _CONCEPTS.values() if concept.title().id == value_id)
                value = concept.title()
            except StopIteration:
                value_json = _CONCEPTS._client.get(
                    f"/{DEFAULT_LANGUAGE}/concepts/get_pref_label?valueid={value_id}"
                ).json()
                concept = _CONCEPTS[value_json["conceptid"]]
                value = concept.values[value_id]
        return value

    @property
    def concept(self) -> "StaticConcept":
        if not self.concept_id:
            raise RuntimeError("No concept for this value. Perhaps a collection title?")
        return _CONCEPTS[self.concept_id]

class StaticCollectionDict(TypedDict):
    """Loading holder for collections."""

    id: NotRequired[UUID]
    title: NotRequired[StaticValue]
    concepts: NotRequired[list[UUID]]

class StaticConceptDict(TypedDict):
    """Loading holder for concepts."""

    id: NotRequired[UUID]
    values: dict[UUID, StaticValue]
    children: NotRequired[list["StaticConcept"]]
    source: Path | None

@dataclass
class StaticCollection:
    """Minimal representation of an Arches collection."""

    id: UUID
    title: StaticValue
    concepts: list[UUID]

@dataclass
class StaticConcept:
    """Minimal representation of an Arches concept."""

    id: UUID
    values: dict[UUID, StaticValue]
    source: Path | None
    children: list["StaticConcept"]

    def title(self, language: str | None = DEFAULT_LANGUAGE) -> StaticValue:
        if language:
            try:
                return next(value for value in self.values.values() if value.language == language)
            except StopIteration:
                ...
        return next(iter(self.values.values()))

class ConceptsDict(UserDict[UUID, StaticConcept]):
    @property
    def _client(self):
        adapter = get_adapter("resource_api")
        return httpx.Client(**adapter.config.get("client", {}))

    def __getitem__(self, key):
        try:
            concept = super().__getitem__(key)
        except KeyError:
            concept_json = self._client.get(
                f"/api/arches/concepts?skos_uuid={key}"
            ).json()
            make_concept(
                concept_json["ConceptID"],
                values={
                    UUID(value["ValueID"]): (
                        (value.get("LanguageID", None).get("String")) or DEFAULT_LANGUAGE,
                        value["Value"]
                    )
                    for value in concept_json["Concepts"]
                    if value["ValueType"] == "prefLabel"
                },
                children=None
            )
            concept = super().__getitem__(UUID(concept_json["ConceptID"]))
        return concept

_CONCEPTS = ConceptsDict()
_RAW_COLLECTIONS: dict[UUID, StaticCollection] = {}

def load_collection_path(concept_root: Path) -> None:
    if concept_root.is_dir():
        for fname in concept_root.iterdir():
            if fname.suffix == ".xml":
                load_collection_path(fname)
    else:
        graph = Graph()
        with concept_root.open() as xml:
            graph.parse(data=xml.read(), format="application/rdf+xml")
        for collection, v, o in graph.triples((None, RDF.type, SKOS.Collection)):
            collection_id = UUID(str(collection).split("/", -1)[-1])
            top_attributes = StaticCollectionDict(id=collection_id, concepts=[])
            for predicate, object in graph.predicate_objects(subject=collection):
                if predicate == SKOS.member:
                    for concept, _, _ in graph.triples((object, RDF.type, SKOS.Concept)):
                        top_attributes["concepts"].append(UUID(concept.split("/", -1)[-1]))
                elif predicate == SKOS.prefLabel:
                    value_dict = json.loads(object.value)
                    title = StaticValue(
                        language=object.language,
                        value=value_dict["value"],
                        id=UUID(value_dict["id"]),
                        concept_id=None
                    )
                    top_attributes["title"] = title
            _RAW_COLLECTIONS[top_attributes["id"]] = StaticCollection(**top_attributes)

def load_concept_path(concept_root: Path) -> None:
    if concept_root.is_dir():
        for fname in concept_root.iterdir():
            if fname.suffix == ".xml":
                load_concept_path(fname)
    else:
        top_concepts = []
        graph = Graph()
        with concept_root.open() as xml:
            graph.parse(data=xml.read(), format="application/rdf+xml")
        for scheme, v, o in graph.triples((None, RDF.type, SKOS.ConceptScheme)):
            top_attributes = StaticConceptDict(children=[], values={}, source=concept_root)
            for predicate, object in graph.predicate_objects(subject=scheme):
                if predicate == SKOS.hasTopConcept:
                    top_concepts.append(UUID(str(object).split("/", -1)[-1]))
                elif predicate == DCTERMS.identifier:
                    top_attributes["id"] = json.loads(object.value)["value"].split("/", -1)[-1]
                elif predicate == DCTERMS.title:
                    value_dict = json.loads(object.value)
                    title_attributes = {
                        "language": object.language,
                        "value": value_dict["value"],
                        "id": UUID(value_dict["id"]),
                    }
            title_attributes["concept_id"] = top_attributes["id"]
            top_attributes["values"] = {title_attributes["id"]: StaticValue(**title_attributes)}
            static_concept =  StaticConcept(**top_attributes)
            _CONCEPTS[top_attributes["id"]] = static_concept
            for s, v, o in graph.triples((None, SKOS.inScheme, scheme)):
                attributes = StaticConceptDict(children=[], values={}, source=None)
                for predicate, object in graph.predicate_objects(subject=s):
                    if predicate == DCTERMS.identifier and hasattr(object, "value"):
                        concept_id = json.loads(object.value)["value"].split("/", -1)[-1]
                        attributes["id"] = UUID(concept_id)
                    elif predicate == SKOS.prefLabel and hasattr(object, "value"):
                        value_dict = json.loads(object.value)
                        value = StaticValue(
                            language=object.language,
                            value=value_dict["value"],
                            id=UUID(value_dict["id"]),
                            concept_id=top_attributes["id"]
                        )
                        attributes["values"][value.id] = value
                _CONCEPTS[attributes["id"]] = StaticConcept(**attributes)
            children = [_CONCEPTS[c] for c in top_concepts]
            static_concept.children += [concept for concept in children if isinstance(concept, StaticConcept)]

def _make_concept(value_id: UUID, collection_id: None | UUID) -> ConceptValueViewModel:
    return ConceptValueViewModel(
        value_id,
        StaticValue.from_concept,
        collection_id if collection_id else None,
        (lambda _: retrieve_collection(collection_id) if collection_id else None),
        lambda concept_id, language: [_make_concept(c.title(language).id, None) for c in _CONCEPTS[concept_id].children]
    )

def retrieve_concept(concept_id: str | UUID) -> ConceptValueViewModel:
    concept_id = UUID(concept_id) if not isinstance(concept_id, UUID) else concept_id
    concept = _CONCEPTS[concept_id]
    value_id = concept.title().id
    return _make_concept(value_id, None)

def retrieve_children(concept_id: UUID, language: str | None, datatype) -> list[ConceptValueViewModel]:
    # RMV TEST
    concept = retrieve_concept(concept_id=concept_id)
    return [
        make_concept_value(concept.get_preflabel().valueid, collection_id=None)
        for child in concept.children
    ]

def make_concept(concept_id: str | UUID, values: dict[UUID, tuple[str, str]], children: list[UUID] | None) -> ConceptValueViewModel:
    concept_id = UUID(concept_id) if not isinstance(concept_id, UUID) else concept_id
    attributes: StaticConceptDict = {
        "id": concept_id,
        "values": {
            id: StaticValue(
                value=value,
                language=lang,
                concept_id=concept_id,
                id=id
            ) for id, (lang, value) in values.items()
        },
        "children": [_CONCEPTS[child] for child in (children or [])],
        "source": None
    }
    concept = StaticConcept(**attributes)
    _CONCEPTS[concept.id] = concept
    return _make_concept(concept.title().id, None)

def invalidate_collection(concept_id):
    if concept_id in _COLLECTIONS:
        del _COLLECTIONS[concept_id]

def retrieve_collection(collection_id: UUID | str, language: None | str = None) -> type[Enum]:
    collection_id = collection_id if isinstance(collection_id, UUID) else UUID(collection_id)
    if collection_id in _COLLECTIONS:
        return _COLLECTIONS[collection_id]
    collection = _RAW_COLLECTIONS[collection_id]
    if not isinstance(collection, StaticCollection):
        raise TypeError("ID corresponds to a concept, not a collection")
    made_collection = make_collection(
        collection.title.value,
        [
            _make_concept(c.title(language).id, collection_id) for concept in
            collection.concepts if isinstance((c := _CONCEPTS[concept]), StaticConcept)
        ],
        str(collection_id)
    )
    _COLLECTIONS[collection_id] = made_collection
    return made_collection

def update_collections(collection: CollectionEnum, source_file: Path, arches_url: str) -> None:
    cgraph = Graph()
    if not hasattr(collection, "__identifier__"):
        raise TypeError("This seems to be a malformed collection, or an unrelated Enum")
    arches_url_prefix = list(urlparse(arches_url))
    arches_url_prefix[2] = "/"
    ARCHES = Namespace(urlunparse(arches_url_prefix))
    if not collection.__identifier__:
        collection.__identifier__ = str(cuuid(ARCHES[collection.__original_name__]))
    identifier = ARCHES[collection.__identifier__]
    try:
        with source_file.open() as xml:
            cgraph.parse(data=xml.read(), format="application/rdf+xml")
    except IOError:
        # RMV handle more clearly
        ...

    cgraph.add((identifier, RDF.type, SKOS.Collection))
    cgraph.add((identifier, SKOS.prefLabel, Literal(json.dumps({
        "id": str(cuuid(f"{identifier}/value")),
        "value": collection.__original_name__,
    }), lang=DEFAULT_LANGUAGE)))
    for key in collection.__members__:
        concept = collection[key].value.concept
        child_identifier = ARCHES[str(concept.id)]
        cgraph.add((identifier, SKOS.member, child_identifier))
        cgraph.add((child_identifier, RDF.type, SKOS.Concept))

    cgraph.bind("skos", Namespace("http://www.w3.org/2004/02/skos/core#"))
    cgraph.bind("rdf", Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#"))
    cgraph.bind("dcterms", Namespace("http://purl.org/dc/terms/"))
    xml_string = cgraph.serialize(format="pretty-xml")
    if isinstance(xml_string, str):
        xml_string = xml_string.encode("utf-8")
    etree = ET.ElementTree(ET.fromstring(xml_string))
    ET.indent(etree)
    etree.write(str(source_file), xml_declaration=True)

def save_concept(concept: ConceptValueViewModel, output_file: Path | None, arches_url: str) -> None:
    static_concept = _CONCEPTS[concept.conceptid]
    output_file = output_file or static_concept.source
    if output_file is None:
        raise RuntimeError(f"Could not save concept {str(concept.title())} as no source/destination - perhaps you meant to use a parent concept?")
    graph = concept_to_skos(static_concept, arches_url)
    xml_string = graph.serialize(format="pretty-xml")
    if isinstance(xml_string, str):
        xml_string = xml_string.encode("utf-8")
    etree = ET.ElementTree(ET.fromstring(xml_string))
    ET.indent(etree)
    etree.write(str(output_file), xml_declaration=True)

def concept_to_skos(concept: StaticConcept, arches_url: str) -> Graph:
    graph = Graph()
    arches_url_prefix = list(urlparse(arches_url))
    arches_url_prefix[2] = "/"
    ARCHES = Namespace(urlunparse(arches_url_prefix))
    identifier = ARCHES[str(concept.id)]
    graph.add((identifier, RDF.type, SKOS.ConceptScheme))
    graph.add((identifier, SKOS.prefLabel, Literal(json.dumps({
        "id": str(cuuid(f"{identifier}/value")),
        "value": concept.title().value,
    }), lang=concept.title().language)))

    graph.add((identifier, DCTERMS.identifier, Literal(json.dumps({
        "id": str(cuuid(f"{identifier}/identifier")),
        "value": identifier
    }), lang="en")))

    for child in concept.children:
        child_identifier = ARCHES[str(child.id)]
        graph.add((identifier, SKOS.hasTopConcept, child_identifier))
        graph.add((child_identifier, RDF.type, SKOS.Concept))
        graph.add((child_identifier, SKOS.prefLabel, Literal(json.dumps({
            "id": str(cuuid(f"{identifier}/{child.id}/value")),
            "value": child.title().value
        }), lang="en")))
        graph.add((child_identifier, DCTERMS.identifier, Literal(json.dumps({
            "id": str(cuuid(f"{identifier}/{child.id}/identifier")),
            "value": child_identifier
        }), lang="en")))

        graph.add((child_identifier, SKOS.inScheme, identifier))

    graph.bind("skos", Namespace("http://www.w3.org/2004/02/skos/core#"))
    graph.bind("rdf", Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#"))
    graph.bind("dcterms", Namespace("http://purl.org/dc/terms/"))
    return graph

@REGISTER("concept-list")
def concept_list(tile, node, value: list[UUID | str] | None, _, __, ___, datatype):
    if value is None:
        value = tile.data.get(str(node.nodeid), []) or []

    collection_id = None
    if node and node.config:
        collection_id = node.config.get("rdmCollection")

    def make_cb(value):
        return REGISTER.make(tile, node, value=value, datatype="concept")[0]

    return ConceptListValueViewModel(
        value, make_cb, collection_id, partial(retrieve_collection)
    )


@concept_list.as_tile_data
def cl_as_tile_data(concept_list):
    return [cv_as_tile_data(x) for x in concept_list]


@REGISTER("concept")
def concept_value(tile, node, value: UUID | str | None | CollectionEnum | ConceptValueViewModel | EmptyConceptValueViewModel, __, ___, ____, datatype) -> ConceptValueViewModel | EmptyConceptValueViewModel | None:
    if value is None:
        value = tile.data.get(str(node.nodeid), None)
    collection_id = None
    if node and node.config:
        collection_id = node.config.get("rdmCollection")
    if isinstance(value, CollectionEnum):
        value = value.value
    if isinstance(value, ConceptValueViewModel | EmptyConceptValueViewModel):
        if value._collection_id != collection_id:
            raise RuntimeError(
                f"Tried to assign value from collection {value._collection_id} to node for collection {collection_id}"
            )
        return value
    return make_concept_value(value if isinstance(value, UUID) else UUID(value) if value else None, collection_id, datatype)

def make_concept_value(value: UUID | None, collection_id: UUID | None, datatype) -> ConceptValueViewModel | EmptyConceptValueViewModel | None:
    def concept_value_cb(value):
        if isinstance(value, ConceptValueViewModel):
            value = value._concept_value_id
        return StaticValue.from_concept(value)

    if value is None or isinstance(value, EmptyConceptValueViewModel):
        if collection_id:
            return EmptyConceptValueViewModel(
                collection_id,
                partial(retrieve_collection)
            )
        return None

    return ConceptValueViewModel(
        value,
        concept_value_cb,
        collection_id,
        partial(retrieve_collection),
        partial(retrieve_children)
    )


@concept_value.as_tile_data
def cv_as_tile_data(concept_value):
    return None if isinstance(concept_value, EmptyConceptValueViewModel) else str(concept_value._concept_value_id)
