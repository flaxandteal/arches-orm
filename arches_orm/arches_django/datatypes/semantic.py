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
    SemanticViewModel,
)
from ._register import REGISTER

@REGISTER("semantic")
def semantic(
    tile,
    node,
    value: uuid.UUID | str | WKRI | Resource | ResourceInstance | None,
    parent,
    child_nodes,
    datatype,
):
    def make_pseudo_node(key):
        return parent._make_pseudo_node(
            key,
            tile=(tile if child_nodes[key][1] else None),  # Does it share a tile
        )

    return SemanticViewModel(
        parent,
        {key: value[1] for key, value in child_nodes.items()},
        value,
        make_pseudo_node,
    )


@semantic.as_tile_data
def sm_as_tile_data(semantic):
    # Ensure all nodes have populated the tile
    tile = None
    for value in semantic.get_children(direct=True):
        tile = value.get_tile() or tile
    data = tile.data if tile is not None else {}
    return data
