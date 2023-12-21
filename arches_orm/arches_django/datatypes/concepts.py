import uuid

from arches_orm.view_models import (
    ConceptListValueViewModel,
    ConceptValueViewModel,
)
from ._register import REGISTER


@REGISTER("concept-list")
def concept_list(tile, node, value: list[uuid.UUID | str] | None, _, __, ___):
    if value is None:
        value = tile.data.get(str(node.nodeid), [])

    def make_cb(value):
        return REGISTER.make(tile, node, value=value, datatype="concept")[0]

    return ConceptListValueViewModel(value, make_cb)


@concept_list.as_tile_data
def cl_as_tile_data(concept_list):
    return [cv_as_tile_data(x) for x in concept_list]


@REGISTER("concept")
def concept_value(tile, node, value: uuid.UUID | str | None, __, ___, datatype):
    if value is None:
        value = tile.data.get(str(node.nodeid), None)
    concept_value_cb = datatype.get_value
    if value is None:
        return None
    return ConceptValueViewModel(value, concept_value_cb)


@concept_value.as_tile_data
def cv_as_tile_data(concept_value):
    return str(concept_value._concept_value_id)
