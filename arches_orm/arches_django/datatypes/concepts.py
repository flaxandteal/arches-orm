
import uuid
from typing import Any, Callable
from functools import cached_property
from django.contrib.auth.models import User
from arches.app.models.models import Node, ResourceInstance
from arches.app.models.tile import Tile
from arches.app.models.resource import Resource
from collections import UserDict

from arches_orm.view_models import (
    WKRI,
    UserViewModelMixin,
    UserProtocol,
    StringViewModel,
    RelatedResourceInstanceListViewModel,
    RelatedResourceInstanceViewModelMixin,
    ConceptListValueViewModel,
    ConceptValueViewModel,
    SemanticViewModel,
)
from ._register import REGISTER

@REGISTER("concept-list")
def concept_list(tile, node, value: list[uuid.UUID | str] | None, _, __, ___):
    if value is None:
        value = tile.data[str(node.nodeid)]
    make_cb = lambda value: REGISTER.make(
        tile,
        node,
        value=value,
        datatype="concept"
    )[0]
    return ConceptListValueViewModel(value, make_cb)


@concept_list.as_tile_data
def cl_as_tile_data(concept_list):
    return [cv_as_tile_data(x) for x in concept_list]


@REGISTER("concept")
def concept_value(tile, node, value: uuid.UUID | str | None, __, ___, datatype):
    if value is None:
        value = tile.data[str(node.nodeid)]
    concept_value_cb = datatype.get_value
    if value is None:
        return None
    return ConceptValueViewModel(value, concept_value_cb)


@concept_value.as_tile_data
def cv_as_tile_data(concept_value):
    return str(concept_value._concept_value_id)
