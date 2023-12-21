from typing import Any, Callable
from functools import cached_property
from arches.app.models.models import Node
from arches.app.models.tile import Tile
from collections import UserDict


class RegisterFunction(Callable):
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
    def __call__(self, typ):
        def wrapper(fn) -> RegisterFunction:
            self[typ] = RegisterFunction(fn)
            return self[typ]

        return wrapper

    @cached_property
    def _datatype_factory(self):
        """Caching datatype factory retrieval (possibly unnecessary)."""
        from arches.app.datatypes.datatypes import DataTypeFactory, ResourceInstanceListDataType

        class DataTypeFactoryWithResourceInstanceList(DataTypeFactory):
            def get_instance(self, datatype):
                if datatype == "resource-instance-list":
                    if "ResourceInstanceListDataType" not in DataTypeFactory._datatype_instances:
                        super().get_instance("resource-instance-list")
                        d_datatype = DataTypeFactory._datatypes["resource-instance-list"]
                        DataTypeFactory._datatype_instances["ResourceInstanceListDataType"] = ResourceInstanceListDataType(d_datatype)
                    return DataTypeFactory._datatype_instances["ResourceInstanceListDataType"]
                return super().get_instance(datatype)
        return DataTypeFactoryWithResourceInstanceList()

    def make(
        self,
        tile: Tile,
        node: Node,
        value: Any = None,
        parent: Any = None,
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

        datatype = self._datatype_factory.get_instance(datatype_name)

        if datatype_name in self:
            registration = self[datatype_name]
            record = registration(tile, node, value, parent, child_nodes, datatype)
            return record, registration.transform_value_for_tile
        else:
            return datatype.transform_value_for_tile(
                value or tile.data, **(node.config or {})
            ), lambda value: datatype.transform_value_for_tile(
                value, **(node.config or {})
            )


def get_view_model_for_datatype(tile, node, parent, child_nodes, value=None):
    return REGISTER.make(
        tile, node, value=value, parent=parent, child_nodes=child_nodes
    )


REGISTER = ViewModelRegister()
