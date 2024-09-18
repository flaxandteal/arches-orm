import logging
import uuid
from functools import partial
from collections import UserList

from arches_orm.adapter import get_adapter
from arches_orm.view_models import (
    ResourceInstanceViewModel,
    SemanticViewModel,
)
from arches_orm.static.datatypes.resource_instances import StaticResource
from ._register import REGISTER


logger = logging.getLogger(__name__)

def make_pseudo_node(svm, key, parent_cls, tile, child_nodes, parent):
    child = parent_cls._._make_pseudo_node_cls(
        key,
        tile=(tile if child_nodes[key][1] else None),  # Does it share a tile
        wkri=parent
    )
    child._parent_node = svm
    if parent:
        parent._._values.setdefault(key, [])
        parent._._values[key].append(child)
    return child

def get_child_values(svm, target_key: str | None = None, parent = None, child_keys = None, child_nodes = None, tile = None, node = None):
    from arches_orm.pseudo_node.pseudo_nodes import PseudoNodeList

    if not parent:
        return {}
    for key in child_keys:
        parent._._values._get(key)
    children = {}
    for key, values in parent._._values.items():
        for value in values:
            if (
                key in child_keys
                and value is not None
                and (value._parent_node is None or value._parent_node is svm)
            ):
                if (
                    (tile and value.parenttile_id == tile.tileid)
                    or (
                        value.node.nodegroup_id == node.nodeid
                        and (tile and value.tile == tile)
                        and child_nodes[key][1]  # It shares a tile
                    )
                ):
                    children[key] = value
                elif (
                    node.nodegroup_id != value.node.nodegroup_id
                    and not child_nodes[key][1]  # It does not share a tile
                ):
                    # This avoids list types that have their own tiles (like resource or concept lists)
                    # from appearing doubly-nested
                    if isinstance(value, PseudoNodeList) or (hasattr(value, 'value') and isinstance(value.value, UserList)):
                        if key in children:
                            children[key] += value
                        else:
                            children[key] = value
                    else:
                        # In this case, we have a value, but the wrapper logic did not make it a PseudoNodeList, so
                        # we should treat it as singular.
                        children[key] = value
    for key, value in children.items():
        value._parent_node = svm
        svm._child_values[key] = value

    if target_key is not None:
        return children.get(target_key, None)
    return children



@REGISTER("semantic")
def semantic(
    tile,
    node,
    value: uuid.UUID | str | ResourceInstanceViewModel | StaticResource | None,
    parent,
    parent_cls,
    child_nodes,
    datatype,
):
    child_keys = {key: child_value[1] for key, child_value in child_nodes.items()}

    svm = SemanticViewModel(
        parent,
        child_keys,
        partial(make_pseudo_node, parent_cls=parent_cls, tile=tile, parent=parent, child_nodes=child_nodes),
        partial(get_child_values, parent=parent, child_keys=child_keys, child_nodes=child_nodes, tile=tile, node=node),
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
