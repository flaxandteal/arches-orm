from __future__ import annotations

import uuid
try:
    from typing import NotRequired
except ImportError: # 3.9
    from typing_extensions import NotRequired

from functools import partial
from arches_orm.collection import CollectionEnum
from arches_orm.view_models.concepts import EmptyConceptValueViewModel, ConceptListValueViewModel, ConceptValueViewModel
from ._register import REGISTER
from .concepts import retrieve_concept, retrieve_collection

def retrieve_children(concept_id: uuid.UUID, language: str | None, datatype) -> list[ConceptValueViewModel]:
    concept = retrieve_concept(concept_id)
    return concept.children

@REGISTER("concept-list")
def concept_list(tile, node, value: list[uuid.UUID | str] | None, _, __, ___, datatype):
    if value is None:
        value = tile.data.get(str(node.nodeid), []) or []

    collection_id = None
    if node and node.config:
        collection_id = uuid.UUID(node.config.get("rdmCollection"))

    def make_cb(value):
        return REGISTER.make(tile, node, value=value, datatype="concept")[0]

    return ConceptListValueViewModel(
        value, make_cb, collection_id, retrieve_collection
    )


@concept_list.as_tile_data
def cl_as_tile_data(concept_list):
    return [cv_as_tile_data(x) for x in concept_list]


@REGISTER("concept")
def concept_value(tile, node, value: uuid.UUID | str | None | CollectionEnum | ConceptValueViewModel | EmptyConceptValueViewModel, __, ___, ____, datatype) -> ConceptValueViewModel | EmptyConceptValueViewModel | None:
    if value is None:
        value = tile.data.get(str(node.nodeid), None)
    collection_id = None
    if node and node.config:
        collection_id = uuid.UUID(node.config.get("rdmCollection"))
    if isinstance(value, CollectionEnum):
        value = value.value
    if isinstance(value, ConceptValueViewModel) or isinstance(value, EmptyConceptValueViewModel):
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
