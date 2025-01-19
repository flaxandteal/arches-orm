from __future__ import annotations
from edtf.parser.parser_classes import Date
from arches_orm.view_models import (
    ExtendedDateViewModel,
)
from ._register import REGISTER


@REGISTER("edtf")
def edtf(tile, node, value: str | Date | None, _, __, ___, edtf_datatype):
    print("EDTF", value, tile)
    if tile:
        tile.data.setdefault(node.nodeid, None)
        if value is not None:
            if isinstance(value, dict):
                tile.data[node.nodeid].update(value)
            else:
                tile.data[node.nodeid] = str(value)

    if not tile or (data := tile.data[node.nodeid]) is None:
        return None
    return ExtendedDateViewModel(data, **node.config)


@edtf.as_tile_data
def e_as_tile_data(edtf_value):
    return str(edtf_value)
