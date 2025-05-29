from __future__ import annotations
from copy import deepcopy
from functools import lru_cache
from collections import UserList
from uuid import UUID

from typing import Any

from arches_orm.view_models import ViewModel, NodeListViewModel, UnavailableViewModel, ResourceInstanceViewModel, SemanticViewModel
from arches_orm.view_models.resources import RelatedResourceInstanceViewModelMixin


class PseudoNodeWrapperMixin:
    @classmethod
    @lru_cache
    def _child_nodes(cls, node_id):
        child_nodes = {}
        node_objects = cls._node_objects()
        edges = cls._edges().get(node_id)
        node = node_objects.get(node_id)
        if edges is not None:
            child_nodes.update(
                {
                    n.alias: (n, not n.is_collector and n.nodegroup_id == node.nodegroup_id)
                    for n in node_objects.values()
                    if n.nodeid in edges
                }
            )
        return child_nodes

    @classmethod
    def _make_pseudo_node_cls(cls, key, single=False, tile=None, wkri=None):
        node_obj = cls._node_objects_by_alias()[key]
        nodegroups = cls._nodegroup_objects()

        permitted = cls._permitted_nodegroups()
        value = None
        if (
            node_obj.nodegroup_id
            and node_obj.is_collector
            and nodegroups[node_obj.nodegroup_id].cardinality == "n"
            and not single
        ):
            value = PseudoNodeList(
                node_obj,
                parent=wkri,
                parent_cls=cls.view_model,
            )
        if value is None or tile:
            if node_obj.nodegroup_id is not None and str(node_obj.nodegroup_id) not in permitted:
                node_value = PseudoNodeUnavailable(
                    node=node_obj,
                    parent=wkri,
                    parent_cls=cls.view_model,
                )
            else:
                child_nodes = cls._child_nodes(node_obj.nodeid)
                inner = False
                if child_nodes and node_obj.datatype != 'semantic':
                    inner = PseudoNodeValue(
                        tile=tile,
                        TileProxyModel=cls.TileProxyModel,
                        get_view_model_for_datatype=cls.get_view_model_for_datatype,
                        node=node_obj,
                        value=None,
                        parent=wkri,
                        parent_cls=cls.view_model,
                        child_nodes=child_nodes,
                        inner=True
                    )
                node_value = PseudoNodeValue(
                    tile=tile,
                    TileProxyModel=cls.TileProxyModel,
                    get_view_model_for_datatype=cls.get_view_model_for_datatype,
                    node=node_obj,
                    value=None,
                    parent=wkri,
                    parent_cls=cls.view_model,
                    child_nodes=None if inner is not False else child_nodes,
                    inner=inner
                )
            # If we have a tile in a list, add it
            if value is not None:
                value.append(node_value)
            else:
                value = node_value

        return value

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
        self.outer = None

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

    def set_accessed(self, tree: bool = True):
        for child in self.get_children():
            child.set_accessed(tree)

    def clear(self):
        self._ghost_children |= {
            entry for entry in self if entry.node.nodegroup_id == self.node.nodeid
        }
        super().clear()
        if self.tile and str(self.node.nodeid) in self.tile.data:
            del self.tile.data[str(self.node.nodeid)]

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

    def __init__(self, node, get_view_model_for_datatype, TileProxyModel: type, tile=None, value=None, parent=None, child_nodes=None, parent_cls=None, inner=None):
        self.node = node
        self.tile = tile

        # TODO: (RMV) confirm that self.tile is None only when created by semantic node(?)
        self.independent = self.tile is None
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
        self._value = value
        self._accessed = False
        self._original_tile = tile
        self._TileProxyModel = TileProxyModel
        self.outer = node.datatype != 'semantic' and child_nodes
        if inner is True:
            self.is_inner = True
            self.inner = None
        else:
            self.is_inner = False
            self.inner = inner
        self._child_nodes = child_nodes

    def __str__(self):
        return f"{{{self.value}}}"

    def __repr__(self):
        return str(self)

    def __deepcopy__(self, memo):
        # We do not copy the value, as this should be derived from the tile anyway.
        return PseudoNodeValue(
            self.node,
            self.get_view_model_for_datatype,
            self._TileProxyModel,
            deepcopy(self.tile),
            None,
            self._parent,
            self._child_nodes,
            self._parent_cls,
            inner=self.inner.__deepcopy__(memo) if self.inner else None
        )

    @property
    def parenttile_id(self):
        return self.tile.parenttile_id if self.tile else None

    def get_tile(self):
        self._update_value()

        if self.inner:
            tile, relationships = self.inner.get_tile()
        else:
            relationships = []
        if self._as_tile_data and self._value is not None:
            tile_value = self._as_tile_data(self._value)
        else:
            tile_value = self._value
        if isinstance(tile_value, tuple):
            relationships = [
                relationship
                if isinstance(relationship, tuple)
                else (self.tile.nodegroup_id, self.node.nodeid, relationship)
                for relationship in tile_value[1]
            ]
            tile_value = tile_value[0]
        if tile_value is None:
            self.tile.data.pop(str(self.node.nodeid), None)
        else:
            self.tile.data[
                str(self.node.nodeid)
            ] = tile_value  # TODO: ensure this works for any value
        tile = self.tile if self.independent else None # RMV: is this the correct interpretation of is_collector?

        return tile, relationships

    def clear(self):
        self._value = None
        if self.tile and self.tile.data and str(self.node.nodeid) in self.tile.data:
            del self.tile.data[str(self.node.nodeid)]

    @property
    def accessed(self) -> bool:
        return self._accessed

    def set_accessed(self, tree=False) -> bool:
        self._accessed = True
        if self.inner:
            self.inner.set_accessed(True)
        if tree:
            for child in self.get_children():
                child.set_accessed(tree)

    def _update_value(self):
        self._accessed = True

        if not self.tile:
            if not self.node:
                raise RuntimeError("Empty tile")
            if self.inner:
                self.tile, self.relationships = self.inner.get_tile()
            else:
                # NB: You may see issues where the nodegroup is null because it is the root node,
                # and a node below is not marked as a collector, so tries to fill its tile in
                # A cardinality n node below the root should be a collector.
                self.tile = self._TileProxyModel(
                    nodegroup_id=self.node.nodegroup_id, tileid=None, data={}, sortorder=self.node.sortorder
                )
                self.relationships = []
        if not self._value_loaded:
            if (
                self._value is None
                and self.tile.data is not None
                and str(self.node.nodeid) in self.tile.data
            ):
                data = self.tile.data[str(self.node.nodeid)]
            else:
                data = self._value

            if self.outer and isinstance(data, dict) and "_" in data:
                outer_data = data["_"]
                self.inner.value.update({k: v for k, v in data.items() if k != "_"})
                data = outer_data
            self._value, self._as_tile_data, self._datatype, self._multiple = self.get_view_model_for_datatype(
                self.tile,
                self.node,
                value=data,
                parent=self._parent,
                parent_cls=self._parent_cls,
                child_nodes=self._child_nodes,
                is_inner=self.is_inner
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
        if self.inner and isinstance(value, dict) and "_" in value:
            self._value = value["_"]
            del value["_"]
            self.inner.value.update(value)
        else:
            self._value = value
        if not isinstance(self._value, ViewModel) or isinstance(self._value, ResourceInstanceViewModel):
            self.get_tile() # is this necessary, as it seems to hydrate what the below overwrites?
        self._value_loaded = True
        self.set_accessed()

    def __len__(self):
        return len(self.get_children())

    def get_type(self):
        self._update_value()
        return self._datatype, self._multiple

    def get_child_types(self):
        self._update_value()
        child_types = {}
        if isinstance(self.value, ViewModel):
            try:
                child_types = self.value.get_child_types()
            except AttributeError:
                ...
        if self.inner:
            child_types.update(self.inner.get_child_types())
        return child_types

    def get_children(self, direct=None):
        children = []
        if self.value:
            try:
                children = self.value.get_children(direct=direct)
            except AttributeError:
                ...
        return children

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
        self.outer = None

    def set_accessed(self, tree: bool = True):
        ...

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
        # TODO: should this be instantiated?
        return UnavailableViewModel

    def __len__(self):
        return 0

    def get_children(self, direct=None):
        return []

def update_tiles(
    resource_id: UUID | str | None, tiles, all_values=None, nodegroup_id=None, root=None, parent=None, permitted_nodegroups: None | list[str]=None
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
            keys_to_delete = [key for key in tile.data if isinstance(tile.data[key], SemanticViewModel)]

            for key in keys_to_delete:
                del tile.data[key]

            if parent and parent.tile != tile and parent.node.nodegroup_id:
                tile.parenttile = parent.tile
            nodegroup_id = tile.nodegroup_id
            tiles.setdefault(nodegroup_id, [])
            relationships += [
                (len(tiles[nodegroup_id]), *relationship)
                for relationship in subrelationships
            ]
            tiles[nodegroup_id].append(tile)
    return relationships, ghost_tiles

