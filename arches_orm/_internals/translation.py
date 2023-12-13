from arches.app.models.resource import Resource
from datetime import datetime
from arches.app.models.models import ResourceXResource, Node, NodeGroup
from arches.app.models.tile import Tile as TileProxyModel
from arches.app.models.system_settings import settings as system_settings
from collections import UserList
from .relations import RelationList
from .view_models import get_view_model_for_datatype


LOAD_FULL_NODE_OBJECTS = True
LOAD_ALL_NODES = True

class PseudoNodeList(UserList):
    def __init__(self, nodegroup):
        super().__init__()
        self.nodegroup = nodegroup

class PseudoNode:
    _value_loaded = False
    _value = None

    def __init__(self, node, tile=None, value=None, parent=None, related_prefetch=None):
        self.node = node
        self.tile = tile
        self._related_prefetch = related_prefetch
        self._parent = parent
        self._value = value

    def get_relationships(self):
        try:
            return self.value.get_relationships() if self.value else []
        except AttributeError:
            return []

    def get_tile(self):
        self._update_value()

        try:
            tile_value = self._value.as_tile_data()
        except AttributeError:
            tile_value = self._value
        self.tile.data[str(self.node.nodeid)] = tile_value # TODO: ensure this works for any value
        return self.tile

    def _update_value(self):
        if not self.tile:
            if not self.node:
                raise RuntimeError("Empty tile")
            self.tile = TileProxyModel(
                nodegroup_id=self.node.nodegroup_id,
                tileid=None,
                data={}
            )
        if not self._value_loaded:
            if self.tile.data is not None and str(self.node.nodeid) in self.tile.data:
                data = self.tile.data[str(self.node.nodeid)]
            else:
                data = self._value
            try:
                self._value = get_view_model_for_datatype(
                    self.tile,
                    self.node,
                    value=data,
                    parent=self._parent,
                    related_prefetch=self._related_prefetch
                )
            except KeyError:
                self._value = self.tile.data[str(self.node.nodeid)]
            self._value_loaded = True

    @property
    def value(self):
        self._update_value()
        return self._value

    @value.setter
    def value(self, value):
        self._value = value
        self._value_loaded = True


class SemanticTile(dict):
    __tile: TileProxyModel

    def __init__(self, tile: TileProxyModel | None=None, nodegroup: NodeGroup | None=None):
        if tile is None:
            if nodegroup is None:
                raise RuntimeError("Must have a tile or nodegroup")
            tile = TileProxyModel(
                dict(
                    data={},
                    nodegroup_id=nodegroup.nodegroupid,
                    tileid=None,
                )
            )
        self.__tile = tile
        self.update(tile.data)

    def __setitem__(self, key, value):
        if not isinstance(value, PseudoNode):
            raise RuntimeError("Can only set PseudoNodes on a SemanticTile")
        setattr(self, key, value)

    def get_tile(self):
        self.__tile.data = self
        return self.__tile



class TranslationMixin:

    """Provides functionality for translating to/from Arches types."""

    def fill_from_resource(self, reload=None, related_prefetch=None):
        """Populate fields from the ID-referenced Arches resource."""

        all_values = {}
        cls = self.__class__
        nodes = cls._build_nodes()
        class_nodes = {node["nodeid"]: key for key, node in nodes.items()}
        if reload is True or (reload is None and self._lazy):
            self.resource = Resource.objects.get(resourceinstanceid=self.id)
        self.resource.load_tiles()

        for tile in self.resource.tiles:
            semantic_values = {}
            semantic_node = None
            for nodeid in tile.data:
                if nodeid in class_nodes:
                    key = class_nodes[nodeid]
                    node = nodes[key]
                    if LOAD_FULL_NODE_OBJECTS:
                        nodegroup = cls._nodegroup_objects()[node["nodegroupid"]]
                        node_obj = cls._node_objects()[nodeid]
                    else:
                        nodegroup = NodeGroup(
                            pk=node["nodegroupid"]
                        )
                        node_obj = Node(
                            pk=nodeid,
                            nodeid=nodeid,
                            nodegroup_id=node["nodegroupid"],
                            graph_id=self.graphid,
                        )
                    (
                        datatype,
                        datatype_name,
                        multiple_values,
                    ) = node["datatype"]

                    if "/" in key:
                        _semantic_node, key = key.split("/")
                        if semantic_node is None:
                            semantic_node = _semantic_node
                        elif semantic_node != _semantic_node:
                            raise RuntimeError(
                                "We should never end up with node values from two"
                                " groups (semantic nodes) in a tile:"
                                f" {semantic_node} and {_semantic_node}"
                            )
                        if "/" in semantic_node:
                            raise NotImplementedError(
                                "No support for nested semantic nodes currently"
                            )
                        values = semantic_values
                    else:
                        values = all_values

                    value = PseudoNode(
                        node_obj,
                        tile,
                        related_prefetch=related_prefetch
                    )
                    if multiple_values:
                        values[key] = PseudoNodeList(nodegroup)
                        values[key].append(value)
                    else:
                        values[key] = value
            if semantic_node:
                all_values.setdefault(str(semantic_node), [])
                all_values[str(semantic_node)].append(
                    PseudoNode(None, tile, value=semantic_values)
                )
        self._values.update(all_values)
        self._filled = True

    def _update_tiles(self, tiles, values, tiles_to_remove, prefix=None):
        """Map data in the well-known resource back to the Arches tiles."""

        relationships = []
        for key, node in self._nodes.items():
            if prefix is not None:
                if not key.startswith(prefix):
                    continue
                prekey, key = key.split("/", -1)
                if "/" in prekey:
                    raise NotImplementedError("Only one level of groupings supported")
            elif "/" in key:
                continue

            if key in values:
                data = {}
                single = False
                value = values[key]
                datatype, datatype_name, multiple_values = node["datatype"]
                if value is None:
                    continue

                # FIXME: this change needs checked
                if datatype_name == "semantic" and multiple_values:
                    tiles.setdefault(node["nodegroupid"], [])
                    if "parentnodegroup_id" in node:
                        parent = tiles.setdefault(
                            node["parentnodegroup_id"],
                            [
                                TileProxyModel(
                                    data={},
                                    nodegroup_id=node["parentnodegroup_id"],
                                    tileid=None,
                                )
                            ],
                        )[0]
                    else:
                        parent = None
                    for entry in value:
                        subtiles = {}
                        if parent:
                            subtiles[parent.nodegroup_id] = [parent]

                        # If we have a dataless version of this node, perhaps because it
                        # is already a parent, we allow it to be filled in.
                        if (
                            tiles[node["nodegroupid"]]
                            and not tiles[node["nodegroupid"]][0].data
                            and tiles[node["nodegroupid"]][0].tiles
                        ):
                            subtiles[node["nodegroupid"]] = [
                                tiles[node["nodegroupid"]][0]
                            ]

                        relationships += self._update_tiles(
                            subtiles, entry.value, tiles_to_remove, prefix=f"{key}/"
                        )
                        if node["nodegroupid"] in subtiles:
                            tiles[node["nodegroupid"]] = list(
                                set(tiles[node["nodegroupid"]])
                                | set(subtiles[node["nodegroupid"]])
                            )
                    # We do not need to do anything here, because
                    # the nodegroup (semantic node) has no separate existence from the
                    # values in the tile in our approach -- if there were values, the
                    # appropriate tile(s) were added with this nodegroupid. For nesting,
                    # this would need to change.
                    continue

                if isinstance(value, PseudoNodeList):
                    values = value
                else:
                    values: list = [value]

                for value in values:
                    # FIXME: we should be able to remove entries if appropriate
                    tile = value.get_tile()
                    if tile in tiles_to_remove:
                        tiles_to_remove.remove(tile)
                    relationships += value.get_relationships()

                    if not single and prefix:
                        raise RuntimeError(
                            "Cannot have field multiplicity inside a grouping (semantic"
                            " node), as it is equivalent to nesting"
                        )

                    if "parentnodegroup_id" in node:
                        parents = tiles.setdefault(
                            node["parentnodegroup_id"],
                            [
                                TileProxyModel(
                                    data={},
                                    nodegroup_id=node["parentnodegroup_id"],
                                    tileid=None,
                                )
                            ],
                        )
                        parent = parents[0]
                    else:
                        parent = None

                    if node["nodegroupid"] in tiles:
                        # if single or not tiles[node["nodegroupid"]].data:
                        if single:
                            data = tile.data
                            tile = tiles[node["nodegroupid"]][0]
                            if tile in tiles_to_remove:
                                tiles_to_remove.remove(tile)
                            if parent and not tile.parenttile:
                                tile.parenttile = parent
                                parent.tiles.append(tile)
                            tile.data.update(data)
                            continue

                    tiles.setdefault(node["nodegroupid"], [])
                    if tile not in tiles[node["nodegroupid"]]:
                        tiles[node["nodegroupid"]].append(tile)
                    if parent and tile not in parent.tiles:
                        parent.tiles.append(tile)
        return relationships

    def to_resource(
        self,
        verbose=False,
        strict=False,
        _no_save=False,
        _known_new=False,
        _do_index=True,
    ):
        """Construct an Arches resource.

        This may be new or existing, for this well-known resource.
        """

        resource = Resource(resourceinstanceid=self.id, graph_id=self.graphid)
        tiles = {}
        if not _known_new:
            for tile in TileProxyModel.objects.filter(resourceinstance=resource):
                tiles.setdefault(str(tile.nodegroup_id), [])
                tiles[str(tile.nodegroup_id)].append(tile)
        tiles_to_remove = sum((ts for ts in tiles.values()), [])

        relationships = self._update_tiles(tiles, self._values, tiles_to_remove)

        # parented tiles are saved hierarchically
        resource.tiles = [
            t
            for t in sum((ts for ts in tiles.values()), [])
            if not t.parenttile and t not in tiles_to_remove
        ]
        for tile in tiles_to_remove:
            if tile.tileid:
                tile.delete()

        if not resource.createdtime:
            resource.createdtime = datetime.now()
        # errors = resource.validate(verbose=verbose, strict=strict)
        # if len(errors):
        #    raise RuntimeError(str(errors))

        # FIXME: potential consequences for thread-safety
        # This is required to avoid e.g. missing related models preventing
        # saving (as we cannot import those via CSV on first step)
        self._pending_relationships = []
        if not _no_save:
            bypass = system_settings.BYPASS_REQUIRED_VALUE_TILE_VALIDATION
            system_settings.BYPASS_REQUIRED_VALUE_TILE_VALIDATION = True
            # all_tiles = resource.tiles
            # parentless_tiles = [tile for tile in all_tiles if not tile.parenttile]
            ## This only solves the problem for _one_ level of nesting
            # if len(all_tiles) > len(parentless_tiles):
            #    resource.tiles = parentless_tiles
            #    resource.save()
            #    resource.tiles = all_tiles

            resource.save()
            self.id = resource.resourceinstanceid
            system_settings.BYPASS_REQUIRED_VALUE_TILE_VALIDATION = bypass
        elif not resource._state.adding:
            self.id = resource.resourceinstanceid

        self.resource = resource

        # for nodegroupid, nodeid, resourceid in relationships:
        for value, related in relationships:
            related.to_resource(verbose=verbose, strict=strict, _no_save=_no_save)
            if _no_save:
                self._pending_relationships.append((value, related, self))
            else:
                # TODO: what happens if the cross already exists for some reason?
                cross = ResourceXResource(
                    resourceinstanceidfrom=resource,
                    resourceinstanceidto=related.resource,
                )
                cross.save()
                value.update(
                    {
                        "resourceId": str(resource.resourceinstanceid),
                        "ontologyProperty": "",
                        "resourceXresourceId": str(cross.resourcexid),
                        "inverseOntologyProperty": "",
                    }
                )
                resource.save()

        return resource
