from __future__ import annotations
from arches_orm.view_models import (
    UrlViewModel,
)
from ._register import REGISTER


@REGISTER("url")
def url(tile, node, value: dict | None, _, __, ___, url_datatype):
    if tile:
        nodeid = str(node.nodeid)
        tile.data.setdefault(nodeid, {})
        if value is not None:
            if isinstance(value, dict):
                tile.data[nodeid].update(value)
            elif isinstance(value, UrlViewModel):
                tile.data[nodeid] = u_as_tile_data(value)
            else:
                tile.data[nodeid] = {
                    "url": str(value),
                    "url_label": str(value),
                }

    if not tile or tile.data[nodeid] is None:
        return None
    return UrlViewModel(tile.data[nodeid].get("url"), tile.data[nodeid].get("url_label"))


@url.as_tile_data
def u_as_tile_data(url):
    return {"url": url.href, "url_label": str(url)}
