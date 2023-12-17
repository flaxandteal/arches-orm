from arches.app.models.tile import Tile as TileProxyModel
from collections import UserList

from arches_orm.view_models import ViewModel, NodeListViewModel

from .datatypes import get_view_model_for_datatype


class PseudoNodeList(UserList):
    def __init__(self, node, parent):
        super().__init__()
        self.node = node
        self.parent = parent

    def value_list(self):
        return NodeListViewModel(self)

    def get_tile(self):
        for pseudo_node in self:
            pseudo_node.get_tile()
        return None

    def __iadd__(self, other):
        other_pn = [
            self.parent._make_pseudo_node(
                self.node.alias,
                single=True,
            )
            if not isinstance(item, PseudoNodeValue)
            else item
            for item in other
        ]
        super().__iadd__(other_pn)

    def append(self, item=None):
        if not isinstance(item, PseudoNodeValue):
            value = self.parent._make_pseudo_node(
                self.node.alias,
                single=True,
            )
            if item is not None:
                value.value = item
            item = value
        super().append(item)
        return item.value

    def get_relationships(self):
        return []

    def get_children(self, direct=None):
        return self


class PseudoNodeValue:
    _value_loaded = False
    _value = None

    def __init__(self, node, tile=None, value=None, parent=None, child_nodes=None):
        self.node = node
        self.tile = tile
        if "Model" in str(self.tile.__class__):
            raise RuntimeError()
        self._parent = parent
        self._child_nodes = child_nodes
        self._value = value

    def __str__(self):
        return f"{{{self.value}}}"

    def __repr__(self):
        return str(self)

    def get_relationships(self):
        try:
            return self.value.get_relationships() if self.value else []
        except AttributeError:
            return []

    def get_tile(self):
        self._update_value()

        if self._as_tile_data:
            tile_value = self._as_tile_data(self._value)
        else:
            tile_value = self._value
        self.tile.data[
            str(self.node.nodeid)
        ] = tile_value  # TODO: ensure this works for any value
        return self.tile if self.node.is_collector else None

    def _update_value(self):
        if not self.tile:
            if not self.node:
                raise RuntimeError("Empty tile")
            self.tile = TileProxyModel(
                nodegroup_id=self.node.nodegroup_id, tileid=None, data={}
            )
        if not self._value_loaded:
            if (
                self._value is None
                and self.tile.data is not None
                and str(self.node.nodeid) in self.tile.data
            ):
                data = self.tile.data[str(self.node.nodeid)]
            else:
                data = self._value

            self._value, self._as_tile_data = get_view_model_for_datatype(
                self.tile,
                self.node,
                value=data,
                parent=self._parent,
                child_nodes=self._child_nodes,
            )
            if self._value is not None:
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
            value, self._as_tile_data = get_view_model_for_datatype(
                self.tile,
                self.node,
                value=value,
                parent=self._parent,
                child_nodes=self._child_nodes,
            )
        self._value = value
        self._value_loaded = True

    def __len__(self):
        return len(self.get_children())

    def get_children(self, direct=None):
        if self.value:
            try:
                return self.value.get_children(direct=direct)
            except AttributeError:
                ...
        return []
