import logging
import uuid
from arches.app.models.models import ResourceInstance
from arches.app.models.resource import Resource

from arches_orm.adapter import get_adapter
from arches_orm.view_models import (
    WKRI,
    SemanticViewModel,
)
from ._register import REGISTER


logger = logging.getLogger(__name__)


@REGISTER("semantic")
def semantic(
    tile,
    node,
    value: uuid.UUID | str | WKRI | Resource | ResourceInstance | None,
    parent,
    parent_cls,
    child_nodes,
    datatype,
):
    child_keys = {key: child_value[1] for key, child_value in child_nodes.items()}

    def make_pseudo_node(key):
        child = parent_cls._make_pseudo_node_cls(
            key,
            tile=(tile if child_nodes[key][1] else None),  # Does it share a tile
            wkri=parent
        )
        child._parent_node = svm
        if parent:
            parent._values.setdefault(key, [])
            parent._values[key].append(child)
        return child

    def get_child_values(svm):
        if not parent:
            return {}
        for key in child_nodes:
            parent._values.get(key)
        children = {
            key: value
            for key, values in parent._values.items()
            for value in values
            if key in child_keys
            and value is not None
            and (value._parent_node is None or value._parent_node == svm)
            and (
                (tile and value.parenttile_id == tile.tileid)
                or (
                    value.node.nodegroup_id == node.nodeid
                    and (tile and value.tile == tile)
                    and child_nodes[key][1]  # It shares a tile
                )
                or (
                    node.nodegroup_id != value.node.nodegroup_id
                    and not child_nodes[key][1]  # It does not share a tile
                )
            )
        }
        for key, value in children.items():
            value._parent_node = svm
            svm._child_values[key] = value

        return children

    svm = SemanticViewModel(
        parent,
        child_keys,
        make_pseudo_node,
        get_child_values,
    )
    if value:
        try:
            svm.update(value)
        except Exception as exc:
            _tile_loading_error("Suppressed a tile loading error: %s (tile: %s; node: %s)", exc, str(tile), str(node))
    svm.get_children()

    return svm


def _tile_loading_error(reason, exc, *args):
    if not get_adapter().config.get("suppress-tile-loading-errors"):
        raise exc
    elif not get_adapter().config.get("silence-tile-loading-errors"):
        logging.warning(reason, exc, *args)

@semantic.as_tile_data
def sm_as_tile_data(semantic):
    # Ensure all nodes have populated the tile
    relationships = []
    for value in semantic.get_children(direct=True):
        # We do not use tile, because a child node will ignore its tile reference.
        _, subrelationships = value.get_tile()
        relationships += subrelationships
    # This is none because the semantic type has no nodal value,
    # only its children have nodal values, and the nodal value of this nodeid should
    # not exist.
    return None, relationships
