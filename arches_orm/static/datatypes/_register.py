from functools import lru_cache
from uuid import UUID
from typing import Any
from arches_orm.datatypes import DataTypeNames, COLLECTS_MULTIPLE_VALUES
from arches_orm.pseudo_node.datatypes._register import ViewModelRegister, Tile, Node
from arches_orm.adapter import get_adapter
from arches_orm.view_models.string import StringViewModel

from .concepts import DEFAULT_LANGUAGE

LANGUAGE_DIRECTION = {
    "en": "ltr",
    "ga": "ltr",
}

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

    def transform_value_for_tile(self, value: Any) -> Any:
        return value

    def get_value(self, value: Any) -> Any:
        return value

    def collects_multiple_values(self) -> bool:
        return self.datatype_name in COLLECTS_MULTIPLE_VALUES

# TODO: move to .string
class StaticStringDataType(StaticDataType):
    def transform_value_for_tile(self, value: Any) -> Any:
        if isinstance(value, StringViewModel):
            value = value._value
        elif isinstance(value, str):
            adapter = get_adapter("static")
            language = DEFAULT_LANGUAGE
            try:
                context = adapter.get_context().get()
                language = (context and context.get("language")) or language
            except LookupError:
                ...
            language_direction = LANGUAGE_DIRECTION.get(language) or "ltr"
            value = {language: {"direction": language_direction, "value": value}}
        return value


    def get_display_value(self, tile: Tile | dict[str | UUID, Any], node: Node, language: None | str = None) -> Any:
        tile_value = super().get_display_value(tile=tile, node=node, language=language)
        adapter = get_adapter("static")
        if language is None:
            language = DEFAULT_LANGUAGE
            try:
                context = adapter.get_context().get()
                language = (context and context.get("language")) or language
            except LookupError:
                ...
        string = tile_value.get(language)
        if string is not None:
            string = string.get("value")
        return string

FACTORIES: dict[DataTypeNames, type[StaticDataType]] = {
    DataTypeNames.STRING: StaticStringDataType
}

class StaticDataTypeFactory:
    @lru_cache
    def get_instance(self, datatype: str) -> StaticDataType:
        datatype_name = DataTypeNames(datatype)
        return (FACTORIES.get(datatype_name) or StaticDataType)(datatype_name)

REGISTER = ViewModelRegister.create_with_factory(StaticDataTypeFactory())

def get_view_model_for_datatype(tile, node, parent, parent_cls, child_nodes, value=None):
    return REGISTER.make(
        tile, node, value=value, parent=parent, parent_cls=parent_cls, child_nodes=child_nodes
    )
