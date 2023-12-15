from arches.app.models.resource import Resource
from functools import lru_cache
from datetime import datetime
from arches.app.models.models import ResourceXResource, Node, NodeGroup, Edge
from arches.app.models.tile import Tile as TileProxyModel
from arches.app.models.system_settings import settings as system_settings
from collections import UserList
from .view_models import ViewModel
from .tile_view_models import get_view_model_for_datatype


LOAD_FULL_NODE_OBJECTS = True
LOAD_ALL_NODES = True


class NodeListViewModel(UserList):
    def __init__(self, nodelist):
        self.nodelist = nodelist

    @property
    def data(self):
        return [node.value for node in self.nodelist]

    def append(self, item=None):
        value = self.nodelist.append(item)
        return value

    def extend(self, other):
        self.nodelist.extend(other)

    def sort(self, /, *args, **kwds):
        self.nodelist.sort(*args, **kwds)

    def reverse(self):
        self.nodelist.reverse()

    def clear(self):
        self.nodelist.clear()

    def remove(self, item):
        self.nodelist.remove(item)

    def pop(self):
        item = self.nodelist.pop()
        return item.value

    def insert(self, i, item):
        value = self.nodelist.insert(i, item)
        return value

    def __setitem__(self, i, item):
        self.nodelist[i] = item

    def __delitem__(self, i):
        del self.nodelist[i]

    def __iadd__(self, other):
        self.nodelist += other


class PseudoNodeList(UserList):
    def __init__(self, node, parent):
        super().__init__()
        self.node = node
        self.parent = parent

    def value_list(self):
        return NodeListViewModel(self)

    def get_tile(self):
        for pseudo_node in self:
            pseudo_node.get_tile()
        return None

    def __iadd__(self, other):
        other_pn = [
            self.parent._make_pseudo_node(
                self.node.alias,
                single=True,
            )
            if not isinstance(item, PseudoNodeValue)
            else item
            for item in other
        ]
        super().__iadd__(other_pn)

    def append(self, item=None):
        if not isinstance(item, PseudoNodeValue):
            value = self.parent._make_pseudo_node(
                self.node.alias,
                single=True,
            )
            if item is not None:
                value.value = item
            item = value
        super().append(item)
        return item.value

    def get_relationships(self):
        return []

    def get_children(self, direct=None):
        return self


class PseudoNodeValue:
    _value_loaded = False
    _value = None

    def __init__(self, node, tile=None, value=None, parent=None, child_nodes=None):
        self.node = node
        self.tile = tile
        if "Model" in str(self.tile.__class__):
            raise RuntimeError()
        self._parent = parent
        self._child_nodes = child_nodes
        self._value = value

    def __str__(self):
        return f"{{{self.value}}}"

    def __repr__(self):
        return str(self)

    def get_relationships(self):
        try:
            return self.value.get_relationships() if self.value else []
        except AttributeError:
            return []

    def get_tile(self):
        self._update_value()

        if self._as_tile_data:
            tile_value = self._as_tile_data(self._value)
        else:
            tile_value = self._value
        self.tile.data[
            str(self.node.nodeid)
        ] = tile_value  # TODO: ensure this works for any value
        return self.tile if self.node.is_collector else None

    def _update_value(self):
        if not self.tile:
            if not self.node:
                raise RuntimeError("Empty tile")
            self.tile = TileProxyModel(
                nodegroup_id=self.node.nodegroup_id, tileid=None, data={}
            )
        if not self._value_loaded:
            if self.tile.data is not None and str(self.node.nodeid) in self.tile.data:
                data = self.tile.data[str(self.node.nodeid)]
            else:
                data = self._value

            self._value, self._as_tile_data = get_view_model_for_datatype(
                self.tile,
                self.node,
                value=data,
                parent=self._parent,
                child_nodes=self._child_nodes,
            )
            if self._value is not None:
                self._value._parent_pseudo_node = self
            if self._value is not None:
                self._value_loaded = True

    @property
    def value(self):
        self._update_value()
        return self._value

    @value.setter
    def value(self, value):
        if not isinstance(value, ViewModel):
            value, self._as_tile_data = get_view_model_for_datatype(
                self.tile,
                self.node,
                value=value,
                parent=self._parent,
                child_nodes=self._child_nodes,
            )
        self._value = value
        self._value_loaded = True

    def __len__(self):
        return len(self.get_children())

    def get_children(self, direct=None):
        if self.value:
            try:
                return self.value.get_children(direct=direct)
            except AttributeError:
                ...
        return []


class TranslationMixin:
    _root_node: Node | None = None
    __datatype_factory = None

    """Provides functionality for translating to/from Arches types."""

    def _update_tiles(
        self, tiles, all_values=None, tiles_to_remove=None, nodegroup_id=None, root=None
    ):
        if not root:
            if not all_values:
                return []
            root = [
                node for node in all_values.values() if node.node.nodegroup_id is None
            ][0]

        relationships = []
        combined_tiles = [root.get_tile()]
        for pseudo_node in root.get_children():
            if len(pseudo_node):
                self._update_tiles(
                    tiles, root=pseudo_node, tiles_to_remove=tiles_to_remove
                )
            elif pseudo_node.node.nodegroup_id != root.node.nodegroup_id:
                combined_tiles.append(pseudo_node.get_tile())
            relationships += pseudo_node.get_relationships()

        for tile in combined_tiles:
            if tile:
                tile.parent = root.node
                nodegroup_id = str(pseudo_node.node.nodegroup_id)
                tiles.setdefault(nodegroup_id, [])
                tiles[nodegroup_id].append(tile)
                if tile in tiles_to_remove:
                    tiles_to_remove.remove(tile)
        return relationships

    def __update_tiles(self, tiles, all_values, tiles_to_remove, nodegroup_id=None):
        """Map data in the well-known resource back to the Arches tiles."""

        relationships = []
        nodegroups = self._nodegroup_objects()
        for key, value in all_values.items():
            # if prefix is not None:
            #    if not key.startswith(prefix):
            #        continue
            #    prekey, key = key.split("/", -1)
            #    if "/" in prekey:
            #        raise NotImplementedError("Only one level of groupings supported")
            # elif "/" in key:
            #    continue
            node_obj = value.node
            if nodegroup_id is not None and str(node_obj.nodegroup_id) != nodegroup_id:
                continue
            nodegroup_id = str(node_obj.nodegroup_id) if node_obj.nodegroup_id else None

            data = {}
            single = False

            # FIXME: this change needs checked
            if isinstance(value, PseudoNodeList):
                values = value
            else:
                values: list = [value]

            for value in values:
                if value._child_nodes and nodegroup_id is not None:
                    tiles.setdefault(nodegroup_id, [])
                    nodegroup = nodegroups[nodegroup_id]
                    if nodegroup.parentnodegroup_id:
                        parent = tiles.setdefault(
                            nodegroup.parentnodegroup_id,
                            [
                                TileProxyModel(
                                    data={},
                                    nodegroup_id=nodegroup.parentnodegroup_id,
                                    tileid=None,
                                )
                            ],
                        )[0]
                    else:
                        parent = None
                    if not isinstance(value, PseudoNodeList):
                        value = [value] if value is not None else []
                    for entry in value:
                        nodegroup = nodegroups[nodegroup_id]
                        subtiles = {}
                        if parent:
                            subtiles[str(parent.nodegroup_id)] = [parent]

                        # If we have a dataless version of this node, perhaps because it
                        # is already a parent, we allow it to be filled in.
                        if (
                            tiles[nodegroup_id]
                            and not tiles[nodegroup_id][0].data
                            and tiles[nodegroup_id][0].tiles
                        ):
                            subtiles[nodegroup_id] = [tiles[nodegroup_id][0]]

                        relationships += self._update_tiles(
                            subtiles,
                            entry.value._child_values,
                            tiles_to_remove,
                            nodegroup_id=nodegroup_id,
                        )
                        for nodegroup_id, subtile in subtiles.items():
                            if subtile:
                                tiles[nodegroup_id] = list(
                                    set(tiles[nodegroup_id]) | set(subtile)
                                )
                    # We do not need to do anything here, because
                    # the nodegroup (semantic node) has no separate existence from the
                    # values in the tile in our approach -- if there were values, the
                    # appropriate tile(s) were added with this nodegroupid. For nesting,
                    # this would need to change.
                    continue

                # FIXME: we should be able to remove entries if appropriate
                tile = value.get_tile()
                if tile in tiles_to_remove:
                    tiles_to_remove.remove(tile)
                relationships += value.get_relationships()

                parent = None
                if node_obj != self._root_node:
                    nodegroup = nodegroups[nodegroup_id]
                    if nodegroup.parentnodegroup_id:
                        parents = tiles.setdefault(
                            nodegroup.parentnodegroup_id,
                            [
                                TileProxyModel(
                                    data={},
                                    nodegroup_id=nodegroup.parentnodegroup_id,
                                    tileid=None,
                                )
                            ],
                        )
                        parent = parents[0]

                if nodegroup_id in tiles:
                    # if single or not tiles[node["nodegroupid"]].data:
                    if single:
                        data = tile.data
                        tile = tiles[nodegroup_id][0]
                        if tile in tiles_to_remove:
                            tiles_to_remove.remove(tile)
                        if parent and not tile.parenttile:
                            tile.parenttile = parent
                            parent.tiles.append(tile)
                        tile.data.update(data)
                        continue

                tiles.setdefault(nodegroup_id, [])
                if tile not in tiles[nodegroup_id]:
                    tiles[nodegroup_id].append(tile)
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
                if tile.data is not None:
                    tiles[str(tile.nodegroup_id)].append(tile)
        tiles_to_remove = sum((ts for ts in tiles.values()), [])

        relationships = self._update_tiles(tiles, self._values, tiles_to_remove)

        # parented tiles are saved hierarchically
        resource.tiles = [
            t
            for t in sum((ts for ts in tiles.values()), [])
            if not t.parenttile and t not in tiles_to_remove and t.nodegroup_id
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

            # This fills out the tiles with None values
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

    @classmethod
    def _datatype_factory(cls):
        """Caching datatype factory retrieval (possibly unnecessary)."""
        if cls.__datatype_factory is None:
            # This will expect initialized Django, so we do not do at module start
            from arches.app.datatypes.datatypes import DataTypeFactory

            cls.__datatype_factory = DataTypeFactory()
        return cls.__datatype_factory

    @classmethod
    @lru_cache
    def _node_objects(cls):
        """Caching retrieval of all Arches nodes for this model."""
        if not LOAD_FULL_NODE_OBJECTS:
            raise RuntimeError("Attempt to load full node objects when asked not to")

        if LOAD_ALL_NODES:
            fltr = {"graph_id": cls.graphid}
        else:
            fltr = {
                "nodeid__in": [node["nodeid"] for node in cls._build_nodes().values()]
            }
        return {str(node.nodeid): node for node in Node.objects.filter(**fltr)}

    @classmethod
    @lru_cache
    def _edges(cls):
        edge_pairs = [
            (str(edge.domainnode_id), str(edge.rangenode_id))
            for edge in Edge.objects.filter(graph_id=cls.graphid)
        ]
        edges = {}
        for domain, rang in edge_pairs:
            edges.setdefault(domain, [])
            edges[domain].append(rang)

        return edges

    @classmethod
    @lru_cache
    def _nodegroup_objects(cls) -> dict[str, NodeGroup]:
        """Caching retrieval of all Arches nodegroups for this model."""
        if not LOAD_FULL_NODE_OBJECTS:
            raise RuntimeError("Attempt to load full node objects when asked not to")

        cls._build_nodes()
        return cls._nodegroup_objects_real

    @classmethod
    def from_resource_instance(cls, resourceinstance, cross_record=None):
        """Build a well-known resource from a resource instance."""
        resource = Resource(resourceinstance.resourceinstanceid)
        return cls.from_resource(resource, cross_record=cross_record)

    @classmethod
    def from_resource(cls, resource, cross_record=None, related_prefetch=None):
        """Build a well-known resource from an Arches resource."""

        nodes = cls._build_nodes()
        node_objs = cls._node_objects()
        wkri = cls(
            id=resource.resourceinstanceid,
            resource=resource,
            cross_record=cross_record,
            related_prefetch=related_prefetch,
        )
        values = cls.values_from_resource(
            nodes,
            node_objs,
            resource,
            related_prefetch=related_prefetch,
            wkri=wkri,
        )
        wkri._values = values
        return wkri

    @property
    def _nodes(self):
        return self._build_nodes()

    @classmethod
    @lru_cache
    def _build_nodes(cls):
        if cls._nodes_real or cls._nodegroup_objects_real:
            raise RuntimeError(
                "Cache should never try and rebuild nodes when non-empty"
            )
        nodes: dict[str, dict] = {}
        nodegroups: dict[str, NodeGroup] = {}
        root_node = None
        if LOAD_FULL_NODE_OBJECTS and LOAD_ALL_NODES:
            datatype_factory = cls._datatype_factory()

            node_objects = cls._node_objects()
            for node_obj in node_objects.values():
                # The root node will not have a nodegroup
                if node_obj.nodegroup_id:
                    nodes[str(node_obj.alias)] = {
                        "nodeid": str(node_obj.nodeid),
                        "nodegroupid": str(node_obj.nodegroup_id),
                    }
                else:
                    root_node = node_obj
                    nodes[str(node_obj.alias)] = {
                        "nodeid": str(node_obj.nodeid),
                        "nodegroupid": None,
                    }
            # Ensure defined nodes overwrite the autoloaded ones
            nodes.update(cls._wkrm.nodes)
            nodegroups.update(
                {
                    str(nodegroup.nodegroupid): nodegroup
                    for nodegroup in NodeGroup.objects.filter(
                        nodegroupid__in=[node["nodegroupid"] for node in nodes.values()]
                    )
                }
            )
            for node in nodes.values():
                if nodegroup := nodegroups.get(str(node["nodegroupid"])):
                    if nodegroup.parentnodegroup_id:
                        node["parentnodegroup_id"] = str(nodegroup.parentnodegroup_id)

                    node_obj = node_objects[node["nodeid"]]
                    if "datatype" not in node:
                        node["datatype"] = (
                            datatype_factory.get_instance(node_obj.datatype),
                            node_obj.datatype,
                            nodegroup.cardinality == "n"
                            and node_obj.nodeid == node_obj.nodegroup_id,
                        )

                    if node_obj.config:
                        node["config"] = node_obj.config
                elif node["nodeid"] == str(root_node.nodeid):
                    node_obj = node_objects[node["nodeid"]]
                    node["datatype"] = (
                        datatype_factory.get_instance(node_obj.datatype),
                        node_obj.datatype,
                        False,
                    )
                else:
                    raise KeyError("Missing nodegroups based on WKRM")

        cls._nodes_real.update(nodes)
        cls._nodegroup_objects_real.update(nodegroups)
        cls._root_node = root_node
        return cls._nodes_real

    @classmethod
    def search(cls, text, fields=None, _total=None):
        """Search ES for resources of this model, and return as well-known resources."""

        from arches.app.search.search_engine_factory import SearchEngineFactory
        from arches.app.views.search import RESOURCES_INDEX
        from arches.app.search.elasticsearch_dsl_builder import (
            Bool,
            Match,
            Query,
            Nested,
            Terms,
        )

        # AGPL Arches
        se = SearchEngineFactory().create()
        # TODO: permitted_nodegroups = get_permitted_nodegroups(request.user)
        permitted_nodegroups = [
            node["nodegroupid"]
            for key, node in cls._build_nodes().items()
            if (fields is None or key in fields)
        ]

        query = Query(se)
        string_filter = Bool()
        string_filter.should(
            Match(field="strings.string", query=text, type="phrase_prefix")
        )
        string_filter.should(
            Match(field="strings.string.folded", query=text, type="phrase_prefix")
        )
        string_filter.filter(
            Terms(field="strings.nodegroup_id", terms=permitted_nodegroups)
        )
        nested_string_filter = Nested(path="strings", query=string_filter)
        total_filter = Bool()
        total_filter.must(nested_string_filter)
        query.add_query(total_filter)
        query.min_score("0.01")

        query.include("resourceinstanceid")
        results = query.search(index=RESOURCES_INDEX, id=None)

        results = [
            hit["_source"]["resourceinstanceid"] for hit in results["hits"]["hits"]
        ]
        total_count = query.count(index=RESOURCES_INDEX)
        return results, total_count

    @classmethod
    def all_ids(cls):
        """Get IDs for all resources of this type."""

        return list(
            Resource.objects.filter(graph_id=cls.graphid).values_list(
                "resourceinstanceid", flat=True
            )
        )

    @classmethod
    def all(cls, related_prefetch=None):
        """Get all resources of this type."""

        resources = Resource.objects.filter(graph_id=cls.graphid).all()
        return [
            cls.from_resource(resource, related_prefetch=related_prefetch)
            for resource in resources
        ]

    @classmethod
    def find(cls, resourceinstanceid):
        """Find an individual well-known resource by instance ID."""
        resource = Resource.objects.get(resourceinstanceid=resourceinstanceid)
        if str(resource.graph_id) != cls.graphid:
            raise RuntimeError(
                f"Using find against wrong resource type: {resource.graph_id} for"
                f" {cls.graphid}"
            )
        if resource:
            return cls.from_resource(resource)
        return None

    def remove(self):
        """When called via a relationship (dot), remove the relationship."""

        if not self._cross_record:
            raise NotImplementedError("This method is only implemented for relations")

        wkfm = self._cross_record["wkriFrom"]
        key = self._cross_record["wkriFromKey"]
        wkfm.save()
        resource = wkfm.to_resource()
        tile = resource.tiles
        nodeid = wkfm._nodes[key]["nodeid"]
        nodegroupid = wkfm._nodes[key]["nodegroupid"]
        for tile in resource.tiles:
            if nodegroupid == str(tile.nodegroup_id):
                ResourceXResource.objects.filter(
                    resourceinstanceidfrom=wkfm.resource,
                    resourceinstanceidto=self.resource,
                ).delete()
                del tile.data[nodeid]

        # This is required to avoid e.g. missing related models preventing
        # saving (as we cannot import those via CSV on first step)
        bypass = system_settings.BYPASS_REQUIRED_VALUE_TILE_VALIDATION
        system_settings.BYPASS_REQUIRED_VALUE_TILE_VALIDATION = True
        resource.save()
        system_settings.BYPASS_REQUIRED_VALUE_TILE_VALIDATION = bypass

    def append(self, _no_save=False):
        """When called via a relationship (dot), append to the relationship."""

        if not self._cross_record:
            raise NotImplementedError("This method is only implemented for relations")

        wkfm = self._cross_record["wkriFrom"]
        key = self._cross_record["wkriFromKey"]
        if not _no_save:
            wkfm.save()
            wkfm.to_resource()
        resource = wkfm.resource
        tile = resource.tiles
        nodeid = wkfm._nodes[key]["nodeid"]
        nodegroupid = wkfm._nodes[key]["nodegroupid"]
        for tile in resource.tiles:
            if nodegroupid == str(tile.nodegroup_id):
                cross = ResourceXResource(
                    resourceinstanceidfrom=wkfm.resource,
                    resourceinstanceidto=self.resource,
                )
                cross.save()
                value = [
                    {
                        "resourceId": str(self.resource.resourceinstanceid),
                        "ontologyProperty": "",
                        "resourceXresourceId": str(cross.resourcexid),
                        "inverseOntologyProperty": "",
                    }
                ]
                tile.data.update({nodeid: value})

        # This is required to avoid e.g. missing related models preventing
        # saving (as we cannot import those via CSV on first step)
        if _no_save:
            bypass = system_settings.BYPASS_REQUIRED_VALUE_TILE_VALIDATION
            system_settings.BYPASS_REQUIRED_VALUE_TILE_VALIDATION = True
            resource.save()
            system_settings.BYPASS_REQUIRED_VALUE_TILE_VALIDATION = bypass
        return wkfm, cross, resource

    @classmethod
    def values_from_resource(
        cls, nodes, node_objs, resource, related_prefetch=None, wkri=None
    ):
        """Populate fields from the ID-referenced Arches resource."""

        all_values = {}
        class_nodes = {node["nodeid"]: key for key, node in nodes.items()}

        # load_tiles thins by user
        resource.tiles = TileProxyModel.objects.filter(resourceinstance=resource)

        for tile in resource.tiles:
            if tile.data:
                for nodeid, node_value in tile.data.items():
                    if nodeid in class_nodes:
                        key = class_nodes[nodeid]

                        if node_value is not None:
                            all_values[key] = cls._make_pseudo_node_cls(
                                key, tile=tile, wkri=wkri
                            )
        return all_values

    @classmethod
    def where(cls, cross_record=None, **kwargs):
        """Do a filtered query returning a list of well-known resources."""
        # TODO: replace with proper query
        unknown_keys = set(kwargs) - set(cls._build_nodes())
        if unknown_keys:
            raise KeyError(f"Unknown key(s) {unknown_keys}")

        if len(kwargs) != 1:
            raise NotImplementedError("Need exactly one filter")

        key = list(kwargs)[0]
        value = kwargs[key]

        tiles = TileProxyModel.objects.filter(
            nodegroup_id=cls._build_nodes()[key]["nodegroupid"],
            data__contains={cls._build_nodes()[key]["nodeid"]: value},
        )
        return [
            cls.from_resource_instance(tile.resourceinstance, cross_record=cross_record)
            for tile in tiles
        ]
