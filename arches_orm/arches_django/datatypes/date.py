from __future__ import annotations
from datetime import datetime
from arches_orm.view_models.datetime import (
    DateTimeViewModel,
)
from ._register import REGISTER


@REGISTER("date")
def date(tile, node, value: str | datetime | None, _, __, ___, date_datatype):
    if tile:
        tile.data.setdefault(str(node.nodeid), None)
        if value is not None:
            if isinstance(value, datetime):
                value = value.astimezone()
                value = value.isoformat(timespec="milliseconds")
            tile.data[str(node.nodeid)] = date_datatype.transform_value_for_tile(str(value))

    if not tile or (data := tile.data[str(node.nodeid)]) is None:
        return None

    value = date_datatype.transform_value_for_tile(data)
    return DateTimeViewModel.parse(value)


@date.as_tile_data
def e_as_tile_data(value):
    if isinstance(value, datetime):
        value = value.astimezone()
        value = value.isoformat(timespec="milliseconds")
    return str(value)
