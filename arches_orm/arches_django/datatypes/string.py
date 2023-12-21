from arches_orm.view_models import (
    StringViewModel,
)
from arches.app.models.tile import Tile as TileProxyModel
from ._register import REGISTER


@REGISTER("string")
def string(tile, node, value: dict | None, _, __, string_datatype):
    if tile:
        tile.data.setdefault(str(node.nodeid), {})
        if value is not None:
            if isinstance(value, dict):
                tile.data[str(node.nodeid)].update(value)
            else:
                tile.data[str(node.nodeid)] = string_datatype.transform_value_for_tile(
                    value
                )

    def _flatten_cb(value, language):
        return string_datatype.get_display_value({
            "data": {str(node.nodeid): value},
            "provisionaledits": {}
        }, node, language=language)

    if not tile or tile.data[str(node.nodeid)] is None:
        return None
    return StringViewModel(tile.data[str(node.nodeid)], _flatten_cb)


@string.as_tile_data
def s_as_tile_data(string):
    return string._value
