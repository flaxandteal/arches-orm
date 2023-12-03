import collections


class RelationList(collections.UserList):
    """Manages a list of related resources on a well-known resource."""

    def __init__(self, related_to, key, nodeid, tileid, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.related_to = related_to
        self.key = key
        self.nodeid = nodeid
        self.tileid = tileid

    def append(self, item):
        """Add a well-known resource to the list."""
        datum = {}
        datum["wkriFrom"] = self.related_to
        datum["wkriFromKey"] = self.key
        datum["wkriFromNodeid"] = self.nodeid
        datum["wkriFromTileid"] = self.tileid
        item._cross_record = datum
        super().append(item)
        return item
