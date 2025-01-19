from __future__ import annotations
from collections import UserList
from uuid import UUID

from typing import Any

from arches_orm.view_models import ViewModel, NodeListViewModel, UnavailableViewModel, ResourceInstanceViewModel
from arches_orm.view_models.resources import RelatedResourceInstanceViewModelMixin


class PseudoNodeList(UserList):
    def __init__(self, node, parent=None, parent_cls=None):
        super().__init__()
        self.node = node
        if isinstance(self.node, PseudoNodeList):
            raise RuntimeError("Cannot make a list of lists")
        if parent_cls is None:
            if parent is None:
                raise RuntimeError("Must have a parent or parent class for a pseudo-node")
            parent_cls = parent.__class__
        self._parent = parent
        self._parent_cls = parent_cls
        self.tile = None
        self._parent_node = None
        self.parenttile_id = None
        self._ghost_children = set()

    def free_ghost_children(self):
        ghost_children = self._ghost_children
        self._ghost_children = set()
        return ghost_children

    @property
    def value(self):
        return NodeListViewModel(self)

    def index(self, x, start=0, end=-1):
        return self._find(x, start, end)[0]

    def _find(self, x, start=0, end=-1):
        if end < 0:
            end += len(self)
        item = [(i, entry) for i, entry in enumerate(self) if i >= start and i <= end and (entry == x or entry.value == x)]
        try:
            loc, entry = item[0]
        except KeyError:
            raise ValueError()
        return loc, entry

    def remove(self, x):
        entry = self._find(x)[1]
        super().remove(entry)

        if entry.node.nodegroup_id == self.node.nodeid:
            self._ghost_children.add(entry)

    def pop(self, i=-1):
        entry = super().pop(i)

        if entry.node.nodegroup_id == self.node.nodeid:
            self._ghost_children.add(entry)

        return entry

    def clear(self):
        self._ghost_children |= {
            entry for entry in self if entry.node.nodegroup_id == self.node.nodeid
        }
        super().clear()
        if self.tile and self.node.nodeid in self.tile.data:
            del self.tile.data[self.node.nodeid]

    @value.setter
    def value(self, iterable):
        self.clear()
        for entry in iterable:
            self.append(entry)
        self.get_tile()

    def get_tile(self):
        for pseudo_node in self:
            pseudo_node.get_tile()
        return None, []

    def __iadd__(self, other):
        other_pn = [
            self._parent_cls._make_pseudo_node_cls(
                self.node.alias,
                single=True,
                wkri=self._parent
            )
            if not isinstance(item, PseudoNodeValue)
            else item
            for item in other
        ]
        super().__iadd__(other_pn)
        return self

    def extend(self, iterable):
        raise NotImplementedError()

    def append(self, item=None):
        return self.insert(len(self), item)

    def insert(self, i, item=None):
        if not isinstance(item, PseudoNodeValue):
            value = self.make_pseudo_node()
            if item is not None:
                value.value = item
            item = value
        super().insert(i, item)
        if not self.parenttile_id:
            self.parenttile_id = item.parenttile_id
        if self.parenttile_id != item.parenttile_id:
            raise RuntimeError("Cannot mix parents in a node list")
        return item.value

    def get_children(self, direct=None):
        return self

    def get_type(self):
        return self.make_pseudo_node().get_type()[0], True

    def make_pseudo_node(self):
        return self._parent_cls._._make_pseudo_node_cls(
            self.node.alias,
            single=True,
            wkri=self._parent
        )

    def get_child_types(self):
        return self.make_pseudo_node().get_child_types()


class PseudoNodeValue:
    _value_loaded = False
    _value = None
    _datatype = None
    _multiple = False
    _as_tile_data = None

    def __init__(self, node, get_view_model_for_datatype, TileProxyModel: type, tile=None, value=None, parent=None, child_nodes=None, parent_cls=None):
        self.node = node
        self.tile = tile
        if self.tile and "Model" in str(self.tile.__class__):
            raise RuntimeError("Should only use Tiles not TileModels")
        if parent_cls is None:
            if parent is None:
                raise RuntimeError("Must have a parent or parent class for a pseudo-node")
            parent_cls = parent.__class__
        self.get_view_model_for_datatype = get_view_model_for_datatype
        self._parent = parent
        self._parent_cls = parent_cls
        self._parent_node = None
        self._child_nodes = child_nodes
        self._value = value
        self._accessed = False
        self._original_tile = tile
        self._TileProxyModel = TileProxyModel

    def __str__(self):
        return f"{{{self.value}}}"

    def __repr__(self):
        return str(self)

    @property
    def parenttile_id(self):
        return self.tile.parenttile_id if self.tile else None

    def get_tile(self):
        self._update_value()

        relationships = []
        if self._as_tile_data and self._value is not None:
            tile_value = self._as_tile_data(self._value)
        else:
            tile_value = self._value
        if isinstance(tile_value, tuple):
            relationships = [
                relationship
                if isinstance(relationship, tuple)
                else ((self.tile.nodegroup_id, self.node.nodeid), relationship)
                for relationship in tile_value[1]
            ]
            tile_value = tile_value[0]
        if tile_value is None:
            self.tile.data.pop(self.node.nodeid, None)
        else:
            self.tile.data[
                self.node.nodeid
            ] = tile_value  # TODO: ensure this works for any value
        tile = self.tile if self.node.is_collector else None

        return tile, relationships

    def clear(self):
        self._value = None
        if self.tile and self.tile.data and self.node.nodeid in self.tile.data:
            del self.tile.data[self.node.nodeid]

    @property
    def accessed(self) -> bool:
        return self._accessed

    def _update_value(self):
        self._accessed = True

        if not self.tile:
            if not self.node:
                raise RuntimeError("Empty tile")
            self.tile = self._TileProxyModel(
                nodegroup_id=self.node.nodegroup_id, tileid=None, data={}, sortorder=self.node.sortorder
            )
            self.relationships = []
        if not self._value_loaded:
            if (
                self._value is None
                and self.tile.data is not None
                and self.node.nodeid in self.tile.data
            ):
                data = self.tile.data[self.node.nodeid]
            else:
                data = self._value

            self._value, self._as_tile_data, self._datatype, self._multiple = self.get_view_model_for_datatype(
                self.tile,
                self.node,
                value=data,
                parent=self._parent,
                parent_cls=self._parent_cls,
                child_nodes=self._child_nodes,
            )
            if self._value is not None and isinstance(self._value, ViewModel):
                self._value._parent_pseudo_node = self
            if self._value is not None:
                self._value_loaded = True

    @property
    def value(self):
        self._update_value()
        return self._value

    @value.setter
    def value(self, value):
        if not isinstance(value, ViewModel) or isinstance(value, ResourceInstanceViewModel):
            self.get_tile()
            value, self._as_tile_data, self._datatype, self._multiple = self.get_view_model_for_datatype(
                self.tile,
                self.node,
                value=value,
                parent=self._parent,
                parent_cls=self._parent_cls,
                child_nodes=self._child_nodes,
            )
        self._value = value
        self._value_loaded = True

    def __len__(self):
        return len(self.get_children())

    def get_type(self):
        self._update_value()
        return self._datatype, self._multiple

    def get_child_types(self):
        self._update_value()
        if isinstance(self.value, ViewModel):
            try:
                return self.value.get_child_types()
            except AttributeError:
                ...
        return {}

    def get_children(self, direct=None):
        if self.value:
            try:
                return self.value.get_children(direct=direct)
            except AttributeError:
                ...
        return []

    def __bool__(self):
        return bool(self.value)

class PseudoNodeUnavailable:
    def __init__(self, node, parent=None, child_nodes=None, parent_cls=None):
        self.node = node
        if parent_cls is None:
            if parent is None:
                raise RuntimeError("Must have a parent or parent class for a pseudo-node")
            parent_cls = parent.__class__
        self._parent = parent
        self._parent_cls = parent_cls
        self._parent_node = None
        self._child_nodes = child_nodes

    def __str__(self):
        return "[UNAVAILABLE]"

    def __repr__(self):
        return str(self)

    @property
    def parenttile_id(self):
        return None

    def get_tile(self):
        raise RuntimeError("Node unavailable, likely due to permissions.")

    def clear(self):
        ...

    @property
    def value(self):
        return UnavailableViewModel

    def __len__(self):
        return 0

    def get_children(self, direct=None):
        return []

def update_tiles(
    resource_id: UUID | str, tiles, all_values=None, nodegroup_id=None, root=None, parent=None, permitted_nodegroups: None | list[str]=None
) -> tuple[list[tuple[int, ...]], set[Any]]:
    if not root:
        if not all_values:
            return [], set()
        root = [
            nodelist[0]
            for nodelist in all_values.values()
            if nodelist[0].node.nodegroup_id is None
        ][0]

    combined_tiles = []
    relationships = []
    ghost_tiles = set()
    if not isinstance(root, PseudoNodeList):
        parent = root
    for pseudo_node in root.get_children():
        if isinstance(pseudo_node.value, RelatedResourceInstanceViewModelMixin):
            # Do not cross between resources. The relationship should
            # be captured. The canonical example of this is a semantic node that
            # gives us a related resource instance.
            t, r = pseudo_node.get_tile()
            combined_tiles.append((t, r))
            continue
        if isinstance(pseudo_node, PseudoNodeList) or pseudo_node.accessed:
            if len(pseudo_node):
                subrelationships, subghost_tiles = update_tiles(
                    resource_id, tiles, root=pseudo_node, parent=parent, permitted_nodegroups=permitted_nodegroups
                )
                relationships += subrelationships
                ghost_tiles |= subghost_tiles
            if isinstance(pseudo_node, PseudoNodeList):
                # Only hold ghost tiles that have been saved.
                ghost_tiles = {
                    tile for ghost in pseudo_node.free_ghost_children()
                    if (tile := ghost.get_tile()[0]) and tile.pk and not tile._state.adding
                }
            else:
                t, r = pseudo_node.get_tile()
                if t is not None and permitted_nodegroups is not None and (t.nodegroup_id is None or str(t.nodegroup_id) not in permitted_nodegroups):
                    # Warn if we can
                    if pseudo_node._original_tile and hasattr(pseudo_node._original_tile, "_original_data"):
                        if t.data == pseudo_node._original_tile._original_data:
                            continue
                    raise RuntimeError(f"Attempt to modify data that this user does not have permissions to: {t.nodegroup_id} in {resource_id}")
                else:
                    combined_tiles.append((t, r))
        # This avoids loading a tile as a set of view models, simply to re-save it.
        elif not isinstance(pseudo_node, PseudoNodeList) and pseudo_node._original_tile:
            # TODO: NOTE THAT THIS DOES NOT CAPTURE RELATIONSHIPS THAT HAVE NOT BEEN ACCESSED
            combined_tiles.append((
                pseudo_node._original_tile,
                []
            ))

    for tile, subrelationships in combined_tiles:
        if tile:
            if parent and parent.tile != tile and parent.node.nodegroup_id:
                tile.parenttile = parent.tile
            nodegroup_id = str(tile.nodegroup_id)
            tiles.setdefault(nodegroup_id, [])
            relationships += [
                (len(tiles[nodegroup_id]), *relationship)
                for relationship in subrelationships
            ]
            tiles[nodegroup_id].append(tile)
    return relationships, ghost_tiles

