from __future__ import annotations
from arches_orm.view_models import (
    NonLocalizedStringViewModel,
)
from ._register import REGISTER


@REGISTER("non-localized-string")
def non_localized_string(tile, node, value: dict | None, _, __, ___, non_localized_string_datatype):
    if tile:
        nodeid = str(node.nodeid)
        tile.data.setdefault(nodeid, {})
        if value is not None:
            if isinstance(value, dict):
                tile.data[nodeid].update(value)
            else:
                tile.data[nodeid] = non_localized_string_datatype.transform_value_for_tile(
                    value
                )

    if not tile or tile.data[nodeid] is None:
        return None
    return NonLocalizedStringViewModel(tile.data[nodeid])


@non_localized_string.as_tile_data
def s_as_tile_data(non_localized_string):
    return str(non_localized_string)
