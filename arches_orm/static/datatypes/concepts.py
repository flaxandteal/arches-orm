from __future__ import annotations

from enum import Enum
from lxml import etree as ET
from functools import lru_cache
import json
import logging
from functools import partial
from urllib.parse import urlparse, urlunparse
from uuid import UUID
from pathlib import Path
from dataclasses import dataclass
from typing import TypedDict, Callable, IO
try:
    from typing import NotRequired
except ImportError: # 3.9
    from typing_extensions import NotRequired

from rdflib import Graph, Literal, Namespace, RDF, URIRef
from rdflib.term import Node
from rdflib.resource import Resource
from rdflib.namespace import SKOS, DCTERMS
from arches_orm.collection import make_collection, CollectionEnum
from arches_orm.utils import consistent_uuid as cuuid
from arches_orm.view_models.concepts import (
    ConceptValueViewModel,
    StaticConcept,
    StaticValue,
    StaticRelationship,
    StaticPrefLabel,
    StaticAltLabel,
    StaticRelated,
    StaticNarrower,
    StaticBroader,
    StaticScopeNote,
    StaticConceptScheme,
    DEFAULT_LANGUAGE,
)

logger = logging.getLogger(__name__)


_COLLECTIONS: dict[UUID, type[Enum]] = {}

@lru_cache
def value_from_concept(value_id: str | UUID) -> StaticValue:
    value_id = UUID(value_id) if isinstance(value_id, str) else value_id
    value: StaticValue
    try:
        concept = next(concept for concept in _CONCEPTS.values() if hasattr(concept, "values") and value_id in concept.values)
        value = concept.values[value_id]
    except StopIteration:
        concept = next(concept for concept in _CONCEPTS.values() if concept.title().id == value_id)
        value = concept.title()
    return value

@lru_cache
def get_concept_children(concept_id: UUID) -> list[StaticConcept]:
    concept = _CONCEPTS[concept_id]
    return [_CONCEPTS[UUID(c.rdf_resource.split("/")[-1])] for c in concept.related if isinstance(c, StaticNarrower)]

class StaticCollectionDict(TypedDict):
    """Loading holder for collections."""

    id: NotRequired[UUID]
    title: NotRequired[StaticValue]
    concepts: NotRequired[list[UUID]]

class StaticConceptDict(TypedDict):
    """Loading holder for concepts."""

    id: NotRequired[UUID]
    values: dict[UUID, StaticValue]
    _children: NotRequired[list["StaticConcept"] | Callable[[], list["StaticConcept"]]]
    source: Path | None
    identifier: NotRequired[str]
    related: list[StaticRelationship]

@dataclass
class StaticCollection:
    """Minimal representation of an Arches collection."""

    id: UUID
    title: StaticValue
    concepts: list[UUID]

_CONCEPTS: dict[UUID, StaticConcept] = {}
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
            collection_id = UUID(str(collection).split("/", -1)[-1].strip())
            top_attributes = StaticCollectionDict(id=collection_id, concepts=[])
            for predicate, object in graph.predicate_objects(subject=collection):
                if predicate == SKOS.member:
                    for concept, _, _ in graph.triples((object, RDF.type, SKOS.Concept)):
                        top_attributes["concepts"].append(UUID(concept.split("/", -1)[-1]))
                elif predicate == SKOS.prefLabel and hasattr(object, "value"):
                    try:
                        value_dict = json.loads(object.value)
                    except json.JSONDecodeError:
                        value_dict = {
                            "id": str(cuuid(f"{collection_id}/{object.value}/{object.language}")),
                            "value": object.value
                        }
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
            top_attributes = StaticConceptDict(_children=[], values={}, source=concept_root, related=[])
            scheme_id = None
            try:
                scheme_id = UUID(scheme.split("/", -1)[-1])
                top_attributes["id"] = scheme_id
            except IndexError:
                ...
            for predicate, object in graph.predicate_objects(subject=scheme):
                if predicate == SKOS.hasTopConcept:
                    top_concepts.append(UUID(str(object).split("/", -1)[-1]))
                elif predicate == DCTERMS.identifier:
                    if "id" not in top_attributes:
                        top_attributes["id"] = UUID(json.loads(object.value)["value"].split("/", -1)[-1])
                    top_attributes["identifier"] = object.value
                elif predicate == DCTERMS.title:
                    try:
                        value_dict = json.loads(object.value)
                    except json.JSONDecodeError:
                        value_dict = {
                            "id": str(cuuid(f"{scheme_id}/{object.value}/{object.language}")),
                            "value": object.value
                        }
                    title_attributes = {
                        "language": object.language,
                        "value": value_dict["value"],
                        "id": UUID(value_dict["id"]),
                    }
            if "id" not in top_attributes:
                continue
            title_attributes["concept_id"] = top_attributes["id"]
            top_attributes["values"] = {title_attributes["id"]: StaticValue(**title_attributes)}
            static_concept =  StaticConceptScheme(**top_attributes)
            _CONCEPTS[top_attributes["id"]] = static_concept
            for s, v, o in graph.triples((None, SKOS.inScheme, scheme)):
                attributes = StaticConceptDict(_children=[], values={}, source=None, related=[])
                concept_id: UUID
                try:
                    concept_id = UUID(s.split("/", -1)[-1])
                    attributes["id"] = concept_id
                except IndexError:
                    ...
                for predicate, object in graph.predicate_objects(subject=s):
                    if predicate == DCTERMS.identifier and hasattr(object, "value"):
                        if "id" not in attributes:
                            concept_id = json.loads(object.value)["value"].split("/", -1)[-1]
                            try:
                                attributes["id"] = UUID(concept_id)
                            except (ValueError, TypeError):
                                pass
                        attributes["identifier"] = object.value
                    elif predicate in (SKOS.related, SKOS.narrower):
                        related_cls: type[StaticRelationship]
                        if predicate == SKOS.related:
                            related_cls = StaticRelated
                        elif predicate == SKOS.narrower:
                            related_cls = StaticNarrower
                        elif predicate == SKOS.broader:
                            related_cls = StaticBroader
                        related = related_cls(
                            rdf_resource=str(object)
                        )
                        attributes["related"].append(related)
                    elif predicate in (SKOS.prefLabel, SKOS.altLabel, SKOS.scopeNote) and hasattr(object, "value"):
                        value_cls: type[StaticValue]
                        if predicate == SKOS.prefLabel:
                            value_cls = StaticPrefLabel
                        elif predicate == SKOS.altLabel:
                            value_cls = StaticAltLabel
                        elif predicate == SKOS.scopeNote:
                            value_cls = StaticScopeNote
                        try:
                            value_dict = json.loads(object.value)
                        except json.JSONDecodeError:
                            value_dict = {
                                "id": str(cuuid(f"{concept_id}/{object.value}/{object.language}")),
                                "value": object.value
                            }
                        value = value_cls(
                            language=object.language,
                            value=value_dict["value"],
                            id=UUID(value_dict["id"]),
                            concept_id=attributes["id"]
                        )
                        attributes["values"][value.id] = value
                    elif predicate in (SKOS.inScheme, RDF.type):
                        continue
                    else:
                        # TODO: sortorder
                        logger.warning("Predicate not recognised for concept %s: %s", top_attributes["id"], predicate)
                attributes["_children"] = partial(get_concept_children, concept_id)
                _CONCEPTS[attributes["id"]] = StaticConcept(**attributes)
            children = [_CONCEPTS[c] for c in top_concepts]
            static_concept._children += [concept for concept in children if isinstance(concept, StaticConcept)]

@lru_cache
def _make_concept_value(value_id: UUID, collection_id: None | UUID) -> ConceptValueViewModel:
    value = ConceptValueViewModel(
        value_id,
        value_from_concept,
        retrieve_concept,
        collection_id if collection_id else None,
        (lambda _: retrieve_collection(collection_id) if collection_id else None),
        lambda concept_id, language: [_make_concept_value(c.title(language).id, None) for c in _CONCEPTS[concept_id].children]
    )
    return value

def retrieve_concept(concept_id: str | UUID) -> StaticConcept:
    concept_id = UUID(concept_id) if not isinstance(concept_id, UUID) else concept_id
    concept = _CONCEPTS[concept_id]
    return concept

def retrieve_concept_value(concept_id: str | UUID) -> ConceptValueViewModel:
    concept = retrieve_concept(concept_id)
    value_id = concept.title().id
    return _make_concept_value(value_id, None)

def make_concept(concept_id: str | UUID, values: dict[UUID, tuple[str, str, Node]], children: list[UUID] | None, arches_url: str, scheme: bool=False) -> ConceptValueViewModel:
    node_classes = {
        SKOS.prefLabel: StaticPrefLabel,
        SKOS.scopeNote: StaticScopeNote,
        SKOS.altLabel: StaticAltLabel,
    }
    arches_url_prefix = list(urlparse(arches_url))
    arches_url_prefix[2] = "/"
    ARCHES = Namespace(urlunparse(arches_url_prefix))
    concept_id = UUID(concept_id) if not isinstance(concept_id, UUID) else concept_id
    attributes: StaticConceptDict = {
        "id": concept_id,
        "values": {
            id: node_classes[node_cls](
                value=value,
                language=lang,
                concept_id=concept_id,
                id=id
            ) for id, (lang, value, node_cls) in values.items()
        },
        "_children": [_CONCEPTS[child] for child in (children or [])],
        "source": None,
        "related": (
            []
            if scheme else
            [StaticNarrower(rdf_resource=str(ARCHES[str(child)])) for child in (children or [])]
        )
    }
    concept = (StaticConceptScheme if scheme else StaticConcept)(**attributes)
    _CONCEPTS[concept.id] = concept
    return _make_concept_value(concept.title().id, None)

def retrieve_collection(collection_id: UUID | str, language: None | str = None) -> type[Enum]:
    collection_id = collection_id if isinstance(collection_id, UUID) else UUID(collection_id)
    if collection_id in _COLLECTIONS:
        return _COLLECTIONS[collection_id]
    made_collection = build_collection(collection_id, language=language)
    _COLLECTIONS[collection_id] = made_collection
    return made_collection

def build_collection(collection_id: UUID | str, include: list[UUID] | None=None, exclude: list[UUID] | None=None, language: None | str = None) -> type[Enum]:
    collection_id = collection_id if isinstance(collection_id, UUID) else UUID(collection_id)
    collection = _RAW_COLLECTIONS[collection_id]
    if not isinstance(collection, StaticCollection):
        raise TypeError("ID corresponds to a concept, not a collection")
    concepts = collection.concepts
    if exclude:
        if set(exclude) - set(concepts):
            raise RuntimeError(f"Asked to remove concepts from {collection_id} that are not present")
        concepts = [c for c in concepts if c not in exclude]
    if include:
        if set(include) & set(concepts):
            raise RuntimeError(f"Asked to insert concepts from {collection_id} that are already present")
        concepts += include

    return make_collection(
        collection.title.value,
        [
            _make_concept_value(c.title(language).id, collection_id) for concept in
            concepts if isinstance((c := _CONCEPTS[concept]), StaticConcept)
        ],
        str(collection_id)
    )

def update_collections(collection: CollectionEnum, source_file: Path, arches_url: str) -> None:
    cgraph = Graph()
    try:
        with source_file.open() as xml:
            cgraph.parse(data=xml.read(), format="application/rdf+xml")
    except IOError:
        # RMV handle more clearly
        ...
    export_collection(collection, source_file, arches_url, cgraph=cgraph)

def export_collection(collection: CollectionEnum, source_file: Path | str | IO, arches_url: str, cgraph: Graph | None = None) -> None:
    if not hasattr(collection, "__identifier__"):
        raise TypeError("This seems to be a malformed collection, or an unrelated Enum")
    arches_url_prefix = list(urlparse(arches_url))
    arches_url_prefix[2] = "/"
    ARCHES = Namespace(urlunparse(arches_url_prefix))
    if not collection.__identifier__:
        collection.__identifier__ = str(cuuid(ARCHES[collection.__original_name__]))
    identifier = ARCHES[collection.__identifier__]
    if cgraph is None:
        cgraph = Graph()

    def _add_concept_members(concept: StaticConcept):
        identifier = ARCHES[str(concept.id)]
        for child in concept.children:
            child_identifier = ARCHES[str(child.id)]
            cgraph.add((identifier, SKOS.member, child_identifier))
            cgraph.add((child_identifier, RDF.type, SKOS.Concept))
            _add_concept_members(child)

    cgraph.add((identifier, RDF.type, SKOS.Collection))
    cgraph.add((identifier, SKOS.prefLabel, Literal(json.dumps({
        "id": str(cuuid(f"{identifier}/value")),
        "value": collection.__original_name__,
    }), lang=DEFAULT_LANGUAGE)))
    for member in collection.__top_members__:
        concept = member.concept
        child_identifier = ARCHES[str(concept.id)]
        cgraph.add((identifier, SKOS.member, child_identifier))
        cgraph.add((child_identifier, RDF.type, SKOS.Concept))
        _add_concept_members(concept)

    cgraph.bind("skos", Namespace("http://www.w3.org/2004/02/skos/core#"))
    cgraph.bind("rdf", Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#"))
    cgraph.bind("dcterms", Namespace("http://purl.org/dc/terms/"))
    xml_string = cgraph.serialize(format="pretty-xml")
    if isinstance(xml_string, str):
        xml_string = xml_string.encode("utf-8")
    etree = ET.ElementTree(ET.fromstring(xml_string))
    ET.indent(etree)
    if isinstance(source_file, Path):
        source_file = str(source_file)
    etree.write(source_file, xml_declaration=True)

def save_concept(concept: ConceptValueViewModel, output_file: Path | None | str, arches_url: str) -> None:
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
    if isinstance(output_file, Path):
        output_file = str(output_file)
    etree.write(output_file, xml_declaration=True)

def concept_to_skos(concept: StaticConcept, arches_url: str) -> Graph:
    graph = Graph()
    arches_url_prefix = list(urlparse(arches_url))
    arches_url_prefix[2] = "/"
    ARCHES = Namespace(urlunparse(arches_url_prefix))

    def _add_concept(child_identifier: URIRef, child: StaticConcept, top: bool=False) -> None:
        if top:
            graph.add((identifier, RDF.type, SKOS.ConceptScheme))
        else:
            graph.add((child_identifier, RDF.type, SKOS.Concept))

        if child.values:
            values = list(child.values.values())
        elif (title := child.title()):
            values = [title]
        else:
            values = []

        title = None
        description = None
        for value in values:
            if not value.id:
                value.id = cuuid(f"{identifier}/{child.id}/{value.value}")
            if value.__type__ == SKOS.prefLabel:
                title = value
            elif value.__type__ == SKOS.scopeNote:
                description = value
            graph.add((child_identifier, value.__type__ or SKOS.prefLabel, Literal(json.dumps({
                "id": str(value.id),
                "value": value.value
            }), lang=value.language)))

        for related in child.related:
            graph.add((child_identifier, related.__type__ or SKOS.related, URIRef(related.rdf_resource)))

        if top:
            if title:
                graph.add((child_identifier, DCTERMS.title, Literal(json.dumps({
                    "id": str(cuuid(f"{identifier}/{child.id}/title")),
                    "value": title.value
                }), lang=value.language)))

            if description:
                graph.add((child_identifier, DCTERMS.description, Literal(json.dumps({
                    "id": str(cuuid(f"{identifier}/{child.id}/description")),
                    "value": description.value
                }), lang=description.language)))

            graph.add((child_identifier, DCTERMS.identifier, Literal(json.dumps({
                "id": str(cuuid(f"{identifier}/{child.id}/identifier")),
                "value": child_identifier
            }), lang="en")))
        else:
            graph.add((child_identifier, SKOS.inScheme, identifier))

        if child.children:
            for grandchild in child.children:
                grandchild_identifier = ARCHES[str(grandchild.id)]
                if top:
                    graph.add((identifier, SKOS.hasTopConcept, grandchild_identifier))
                _add_concept(grandchild_identifier, grandchild)


    identifier = ARCHES[str(concept.id)]
    _add_concept(identifier, concept, top=True)
    graph.bind("skos", Namespace("http://www.w3.org/2004/02/skos/core#"))
    graph.bind("rdf", Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#"))
    graph.bind("dcterms", Namespace("http://purl.org/dc/terms/"))
    return graph

def get_concepts_by_label(label: str, pref_only: bool=False) -> list[ConceptValueViewModel]:
    concepts = []
    for concept in _CONCEPTS.values():
        if (title := concept.title()) and title.value == label:
            concepts.append(title.id)
        else:
            for value in concept.values:
                if isinstance(value, StaticPrefLabel) or (not pref_only and isinstance(value, StaticAltLabel)):
                    if value.value == label:
                        concepts.append(value.id)
    return [_make_concept_value(vid, None) for vid in concepts]

def get_collections_by_label(label: str, pref_only: bool=False, language: str | None=None) -> list[type[Enum]]:
    collections = []
    for collection in _RAW_COLLECTIONS.values():
        if collection.title.value == label:
            collections.append(collection.id)
    return [retrieve_collection(cid, language=language) for cid in collections]
