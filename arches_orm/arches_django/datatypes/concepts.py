import uuid
from functools import lru_cache

from arches.app.models.concept import Concept

from arches_orm.view_models import (
    ConceptListValueViewModel,
    ConceptValueViewModel,
    EmptyConceptValueViewModel,
)
from arches_orm.collection import make_collection
from ._register import REGISTER

@lru_cache
def retrieve_collection(concept_id):
    collection = Concept().get(id=concept_id, include=["label"])
    datatype = REGISTER._datatype_factory.get_instance("concept")
    def _make_concept(id, collection_id):
        return ConceptValueViewModel(
            id,
            lambda value_id: datatype.get_value(value_id),
            collection_id if collection_id else None,
            (lambda _: retrieve_collection(collection_id)) if collection_id else None
        )
    return make_collection(
        collection.get_preflabel().value,
        _make_concept(concept_id, None),
        [
            _make_concept(concept[2], concept_id) for concept in
            Concept().get_child_collections(concept_id)
        ]
    )


@REGISTER("concept-list")
def concept_list(tile, node, value: list[uuid.UUID | str] | None, _, __, ___, ____):
    if value is None:
        value = tile.data.get(str(node.nodeid), []) or []

    collection_id = None
    if node and node.config:
        collection_id = node.config.get("rdmCollection")

    def make_cb(value):
        return REGISTER.make(tile, node, value=value, datatype="concept")[0]

    return ConceptListValueViewModel(value, make_cb, collection_id, retrieve_collection)


@concept_list.as_tile_data
def cl_as_tile_data(concept_list):
    return [cv_as_tile_data(x) for x in concept_list]


@REGISTER("concept")
def concept_value(tile, node, value: uuid.UUID | str | None, __, ___, ____, datatype):
    if value is None:
        value = tile.data.get(str(node.nodeid), None)
    def concept_value_cb(value):
        if isinstance(value, ConceptValueViewModel):
            value = value._concept_value_id
        return datatype.get_value(value)

    collection_id = None
    if node and node.config:
        collection_id = node.config.get("rdmCollection")

    if value is None or isinstance(value, EmptyConceptValueViewModel):
        if collection_id:
            return EmptyConceptValueViewModel(
                collection_id,
                retrieve_collection
            )
        return None
    return ConceptValueViewModel(
        value,
        concept_value_cb,
        collection_id,
        retrieve_collection
    )


@concept_value.as_tile_data
def cv_as_tile_data(concept_value):
    return None if isinstance(concept_value, EmptyConceptValueViewModel) else str(concept_value._concept_value_id)
