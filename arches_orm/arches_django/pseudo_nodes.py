from arches.app.models.tile import Tile as TileProxyModel
from collections import UserList

from arches_orm.view_models import ViewModel, NodeListViewModel, UnavailableViewModel

from .datatypes import get_view_model_for_datatype


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

    @property
    def value(self):
        return NodeListViewModel(self)

    def clear(self):
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

    def append(self, item=None):
        if not isinstance(item, PseudoNodeValue):
            value = self.make_pseudo_node()
            if item is not None:
                value.value = item
            item = value
        super().append(item)
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
        return self._parent_cls._make_pseudo_node_cls(
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

    def __init__(self, node, tile=None, value=None, parent=None, child_nodes=None, parent_cls=None):
        self.node = node
        self.tile = tile
        if self.tile and "Model" in str(self.tile.__class__):
            raise RuntimeError("Should only use Tiles not TileModels")
        if parent_cls is None:
            if parent is None:
                raise RuntimeError("Must have a parent or parent class for a pseudo-node")
            parent_cls = parent.__class__
        self._parent = parent
        self._parent_cls = parent_cls
        self._parent_node = None
        self._child_nodes = child_nodes
        self._value = value
        self._accessed = False
        self._original_tile = tile

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
                else (str(self.tile.nodegroup_id), str(self.node.nodeid), relationship)
                for relationship in tile_value[1]
            ]
            tile_value = tile_value[0]
        if tile_value is None:
            self.tile.data.pop(self.node.nodeid, None)
        else:
            self.tile.data[
                str(self.node.nodeid)
            ] = tile_value  # TODO: ensure this works for any value
        tile = self.tile if self.node.is_collector else None
        return tile, relationships

    def clear(self):
        self._value = None
        if self.tile and self.tile.data and str(self.node.nodeid) in self.tile.data:
            del self.tile.data[str(self.node.nodeid)]

    @property
    def accessed(self) -> bool:
        return self._accessed

    def _update_value(self):
        self._accessed = True

        if not self.tile:
            if not self.node:
                raise RuntimeError("Empty tile")
            self.tile = TileProxyModel(
                nodegroup_id=self.node.nodegroup_id, tileid=None, data={}
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

            self._value, self._as_tile_data, self._datatype, self._multiple = get_view_model_for_datatype(
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
        if not isinstance(value, ViewModel):
            self.get_tile()
            value, self._as_tile_data, self._datatype, self._multiple = get_view_model_for_datatype(
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
