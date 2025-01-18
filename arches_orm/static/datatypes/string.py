from __future__ import annotations
from arches_orm.view_models import (
    StringViewModel,
)
from ._register import REGISTER


@REGISTER("string")
def string(tile, node, value: dict | None, _, __, ___, string_datatype):
    if tile:
        tile.data.setdefault(node.nodeid, {})
        if value is not None:
            if isinstance(value, dict):
                tile.data[node.nodeid].update(value)
            else:
                tile.data[node.nodeid] = string_datatype.transform_value_for_tile(
                    value
                )

    def _flatten_cb(value, language):
        return string_datatype.get_display_value(
            {"data": {node.nodeid: value}, "provisionaledits": {}},
            node,
            language=language,
        )

    if not tile or tile.data[node.nodeid] is None:
        return None
    return StringViewModel(tile.data[node.nodeid], _flatten_cb)


@string.as_tile_data
def s_as_tile_data(string):
    return string._value
