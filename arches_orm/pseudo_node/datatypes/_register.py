from typing import Any
from functools import cached_property
from arches_orm.pseudo_node.protocols import Node, Tile, DataTypeFactory
from collections import UserDict


class RegisterFunction:
    def __init__(self, fn):
        self.fn = fn

    def __call__(self, *args, **kwargs):
        return self.fn(*args, **kwargs)

    def as_tile_data(self, as_tile_data_fn):
        self.as_tile_data_fn = as_tile_data_fn
        return as_tile_data_fn

    def transform_value_for_tile(self, value):
        return self.as_tile_data_fn(value)


class ViewModelRegister(UserDict):
    _datatype_factory: None

    def __call__(self, typ):
        def wrapper(fn) -> RegisterFunction:
            self[typ] = RegisterFunction(fn)
            return self[typ]

        return wrapper

    @classmethod
    def create_with_factory(cls, datatype_factory: DataTypeFactory):
        slf = cls()
        slf._datatype_factory = datatype_factory
        return slf

    def make(
        self,
        tile: Tile,
        node: Node,
        value: Any = None,
        parent: Any = None,
        parent_cls: Any = None,
        child_nodes: list = None,
        datatype: str = None,
    ):
        datatype_name = datatype or node.datatype

        # TODO: this seems to an Arches issue?
        # Maybe intended: https://github.com/archesproject/arches/   \
        #       blob/a1c2b429f5aaa54af95a4111862eb87d56709107/arches \
        #       /app/models/migrations/5668_add_resourceinstancelist.py#L25
        if datatype_name == "resource-instance" and (
            (isinstance(value, list))
            or (
                value is None
                and tile.data is not None
                and isinstance(tile.data.get(str(node.nodeid)), list)
            )
        ):
            datatype_name = "resource-instance-list"

        if self._datatype_factory is None:
            raise RuntimeError("Datatype register requires a datatype factory")

        datatype = self._datatype_factory.get_instance(datatype_name)

        if datatype_name in self:
            registration = self[datatype_name]
            record = registration(tile, node, value, parent, parent_cls, child_nodes, datatype)
            return record, registration.transform_value_for_tile, datatype_name, datatype.collects_multiple_values()
        else:
            if value or (tile and tile.data.get(node.nodeid)):
                transformed = datatype.transform_value_for_tile(
                    value or tile.data, **(node.config or {})
                )
            else:
                transformed = None
            return transformed, lambda value: datatype.transform_value_for_tile(
                value, **(node.config or {})
            ), datatype_name, datatype.collects_multiple_values()
