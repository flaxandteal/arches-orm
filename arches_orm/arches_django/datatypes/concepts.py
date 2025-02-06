import uuid
from enum import Enum
from functools import partial

from arches.app.models.concept import Concept

from arches_orm.view_models import (
    ConceptListValueViewModel,
    ConceptValueViewModel,
    EmptyConceptValueViewModel,
)
from arches_orm.collection import make_collection, CollectionEnum
from ._register import REGISTER

_COLLECTIONS: dict[str, type[Enum]] = {}

def invalidate_collection(concept_id):

    print('invalidate_collection | concept_id | ', concept_id)
    print('invalidate_collection | _COLLECTIONS | ', _COLLECTIONS)

    if concept_id in _COLLECTIONS:
        del _COLLECTIONS[concept_id]

def retrieve_children(concept_id: uuid.UUID, language: str | None, datatype) -> list[ConceptValueViewModel]:
    # RMV TEST
    concept = Concept().get(id=concept_id, include=["label"])
    print('retrieve_children | concept | ', concept)

    return [
        make_concept_value(concept.get_preflabel().valueid, collection_id=None, datatype=datatype)
        for child in concept.children
    ]

def retrieve_collection(collection_id: uuid.UUID, datatype=None) -> type[Enum]:
    print('retrieve_collection | collection_id | ', collection_id)
    print('retrieve_collection | datatype | ', datatype)


    if collection_id in _COLLECTIONS:
        return _COLLECTIONS[str(collection_id)]
    collection = Concept().get(id=collection_id, include=["label"])
    if not datatype:
        datatype = REGISTER._datatype_factory.get_instance("concept")
    def _make_concept(id, collection_id):
        return ConceptValueViewModel(
            id,
            lambda value_id: datatype.get_value(value_id),
            collection_id if collection_id else None,
            (lambda _: retrieve_collection(collection_id, datatype=datatype) if collection_id else None),
            partial(retrieve_children, datatype=datatype)
        )
    made_collection = make_collection(
        collection.get_preflabel().value,
        [
            _make_concept(concept[2], collection_id) for concept in
            Concept().get_child_collections(collection_id)
        ],
        str(collection_id)
    )
    _COLLECTIONS[str(collection_id)] = made_collection

    print('retrieve_collection | _COLLECTIONS | ', _COLLECTIONS)

    return made_collection


@REGISTER("concept-list")
def concept_list(tile, node, value: list[uuid.UUID | str] | None, _, __, ___, datatype):
    print('concept_list | tile | ', tile)
    print('concept_list | value | ', value)
    print('concept_list | datatype | ', datatype)
    print('concept_list | node | ', node)

    if value is None:
        value = tile.data.get(str(node.nodeid), []) or []

    collection_id = None
    if node and node.config:
        collection_id = node.config.get("rdmCollection")

    def make_cb(value):
        return REGISTER.make(tile, node, value=value, datatype="concept")[0]

    return ConceptListValueViewModel(
        value, make_cb, collection_id, partial(retrieve_collection, datatype=datatype)
    )


@concept_list.as_tile_data
def cl_as_tile_data(concept_list):
    print('cl_as_tile_data | concept_list | ', concept_list)

    return [cv_as_tile_data(x) for x in concept_list]


@REGISTER("concept")
def concept_value(tile, node, value: uuid.UUID | str | None | CollectionEnum | ConceptValueViewModel | EmptyConceptValueViewModel, __, ___, ____, datatype) -> ConceptValueViewModel | EmptyConceptValueViewModel | None:
    
    # print('concept_value | value | ', value)
    # print('concept_value | node | ', node)
    # print('concept_value | tile | ', tile)

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
    return make_concept_value(value if isinstance(value, uuid.UUID) else uuid.UUID(value) if value else None, collection_id, datatype)

def make_concept_value(value: uuid.UUID | None, collection_id: uuid.UUID | None, datatype) -> ConceptValueViewModel | EmptyConceptValueViewModel | None:
    def concept_value_cb(value):
        if isinstance(value, ConceptValueViewModel):
            value = value._concept_value_id
        return datatype.get_value(value)

    if value is None or isinstance(value, EmptyConceptValueViewModel):
        if collection_id:
            return EmptyConceptValueViewModel(
                collection_id,
                partial(retrieve_collection, datatype=datatype)
            )
        return None
    return ConceptValueViewModel(
        value,
        concept_value_cb,
        collection_id,
        partial(retrieve_collection, datatype=datatype),
        partial(retrieve_children, datatype=datatype)
    )


@concept_value.as_tile_data
def cv_as_tile_data(concept_value):
    print('cv_as_tile_data | concept_value | ', concept_value)
    return None if isinstance(concept_value, EmptyConceptValueViewModel) else str(concept_value._concept_value_id)
