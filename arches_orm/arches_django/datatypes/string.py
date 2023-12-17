from arches_orm.view_models import (
    StringViewModel,
)
from ._register import REGISTER


@REGISTER("string")
def string(tile, node, value: dict | None, _, __, string_datatype):
    tile.data.setdefault(str(node.nodeid), {})
    if value is not None:
        if isinstance(value, dict):
            tile.data[str(node.nodeid)].update(value)
        else:
            tile.data[str(node.nodeid)] = string_datatype.transform_value_for_tile(
                value
            )

    def _flatten_cb(value, language):
        tile.data[str(node.nodeid)] = tile.data[str(node.nodeid)] or {}
        tile.data[str(node.nodeid)].update(value)
        return string_datatype.get_display_value(tile, node, language=language)

    if tile.data[str(node.nodeid)] is None:
        return None
    return StringViewModel(tile.data[str(node.nodeid)], _flatten_cb)


@string.as_tile_data
def s_as_tile_data(string):
    return string._value
