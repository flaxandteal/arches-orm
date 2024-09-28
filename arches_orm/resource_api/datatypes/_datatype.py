from uuid import UUID
from typing import Any
from arches_orm.datatypes import DataTypeNames, COLLECTS_MULTIPLE_VALUES
from arches_orm.pseudo_node.datatypes._register import Tile, Node

class StaticDataType:
    datatype_name: DataTypeNames

    def __init__(self, datatype: DataTypeNames):
        self.datatype_name = datatype

    def get_display_value(self, tile: Tile | dict[str | UUID, Any], node: Node, language: None | str = None) -> Any:
        if isinstance(tile, dict):
            data = tile["data"]
        else:
            data = tile.data
        return data[node.nodeid]

    def transform_value_for_tile(self, value: Any, **kwargs: Any) -> Any:
        return value

    def get_value(self, value: Any) -> Any:
        return value

    def collects_multiple_values(self) -> bool:
        return self.datatype_name in COLLECTS_MULTIPLE_VALUES
