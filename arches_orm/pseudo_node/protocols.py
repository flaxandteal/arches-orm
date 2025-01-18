from __future__ import annotations
from typing import Protocol, Any
from uuid import UUID

class Node(Protocol):
    nodeid: str | UUID
    datatype: str

class Tile(Protocol):
    data: dict[str | UUID, Any]

class DataType(Protocol):
    def get_display_value(self, tile: Tile, node: Node, language: None | str = None) -> Any:
        ...

    def transform_value_for_tile(self, value: Any) -> Any:
        ...

    def get_value(self, value: Any) -> Any:
        ...

    def collects_multiple_values(self) -> bool:
        ...

class DataTypeFactory(Protocol):
    def get_instance(self, datatype_name: str) -> DataType:
        ...
