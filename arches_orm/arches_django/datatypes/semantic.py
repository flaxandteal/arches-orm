import uuid
from arches.app.models.models import ResourceInstance
from arches.app.models.resource import Resource

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
    child_keys = {key: value[1] for key, value in child_nodes.items()}

    def make_pseudo_node(key):
        child = parent._make_pseudo_node(
            key,
            tile=(tile if child_nodes[key][1] else None),  # Does it share a tile
        )
        child._parent_node = svm
        parent._values.setdefault(key, [])
        parent._values[key].append(child)
        return child

    def get_child_values(svm):
        children = {
            key: value
            for key, values in parent._values.items()
            for value in values
            if key in child_keys
            and value is not None
            and value._parent_node is None
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
            if key in svm._child_values:
                raise RuntimeError(
                    "Semantic view model construction error - "
                    f"duplicate keys outside node list: {key}"
                )
            svm._child_values[key] = value

        return children

    svm = SemanticViewModel(
        parent,
        child_keys,
        value,
        make_pseudo_node,
        get_child_values,
    )
    svm.get_children()

    return svm


@semantic.as_tile_data
def sm_as_tile_data(semantic):
    # Ensure all nodes have populated the tile
    relationships = []
    for value in semantic.get_children(direct=True):
        # We do not use tile, because a child node will ignore its tile reference.
        tile, subrelationships = value.get_tile()
        relationships += subrelationships
    return None, relationships
