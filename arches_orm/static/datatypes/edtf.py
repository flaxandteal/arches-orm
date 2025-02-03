from __future__ import annotations
from edtf.parser.parser_classes import Date
from arches_orm.view_models import (
    make_edtf,
)
from ._register import REGISTER


@REGISTER("edtf")
def edtf(tile, node, value: str | Date | None, _, __, ___, edtf_datatype):
    if tile:
        tile.data.setdefault(str(node.nodeid), None)
        if value is not None:
            if isinstance(value, dict):
                tile.data[str(node.nodeid)].update(value)
            else:
                tile.data[str(node.nodeid)] = str(value)

    if not tile or (data := tile.data[str(node.nodeid)]) is None or not data:
        return None
    return make_edtf(data, **node.config)


@edtf.as_tile_data
def e_as_tile_data(edtf_value):
    return str(edtf_value)
