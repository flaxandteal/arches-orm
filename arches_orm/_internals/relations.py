import collections
import uuid
from typing import Protocol


class RelationList(collections.UserList):
    """Manages a list of related resources on a well-known resource."""

    def __init__(self, related_to, key, nodeid, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.related_to = related_to
        self.key = key
        self.nodeid = nodeid

    def append(self, item, tile):
        """Add a well-known resource to the list."""
        datum = {}
        datum["wkriFrom"] = self.related_to
        datum["wkriFromKey"] = self.key
        datum["wkriFromNodeid"] = self.nodeid
        datum["wkriFromTile"] = self.tile
        item._cross_record = datum
        super().append(item)
        return item

class WKRI(Protocol):
    graph_id: uuid.UUID
    _cross_record: dict | None = None
