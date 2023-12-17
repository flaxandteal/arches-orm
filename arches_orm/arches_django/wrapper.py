from arches.app.models.resource import Resource
from django.dispatch import Signal
from functools import lru_cache
from datetime import datetime
from arches.app.models.models import ResourceXResource, Node, NodeGroup, Edge
from arches.app.models.tile import Tile as TileProxyModel
from arches.app.models.system_settings import settings as system_settings
import logging

from arches_orm.wrapper import ResourceWrapper

from .adapter import ArchesDjangoAdapter
from .pseudo_nodes import PseudoNodeList, PseudoNodeValue

logger = logging.getLogger(__name__)


LOAD_FULL_NODE_OBJECTS = True
LOAD_ALL_NODES = True

class ArchesDjangoResourceWrapper(ResourceWrapper, proxy=True):
    _nodes_real: dict = None
    _nodegroup_objects_real: dict = None
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

    @property
    def _nodes(self):
        return self._node_objects_by_alias()

    @classmethod
    @lru_cache
    def _node_objects_by_alias(cls):
        if hasattr(cls.__bases__[0], "_node_objects_by_alias") and cls.proxy:
            return cls.__bases__[0]._node_objects_by_alias()

        return {node.alias: node for node in cls._node_objects().values()}

    @classmethod
    @lru_cache
    def _node_objects(cls):
        """Caching retrieval of all Arches nodes for this model."""

        if hasattr(cls.__bases__[0], "_node_objects") and cls.proxy:
            return cls.__bases__[0]._node_objects()

        if not LOAD_FULL_NODE_OBJECTS:
            raise RuntimeError("Attempt to load full node objects when asked not to")

        cls._build_nodes()
        return cls._nodes_real

    @classmethod
    @lru_cache
    def _edges(cls):
        if hasattr(cls.__bases__[0], "_edges") and cls.proxy:
            return cls.__bases__[0]._edges()

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

        if hasattr(cls.__bases__[0], "_nodegroup_objects") and cls.proxy:
            return cls.__bases__[0]._nodegroup_objects()

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

        node_objs = cls._node_objects()
        wkri = cls(
            id=resource.resourceinstanceid,
            resource=resource,
            cross_record=cross_record,
            related_prefetch=related_prefetch,
        )
        values = cls.values_from_resource(
            node_objs,
            resource,
            related_prefetch=related_prefetch,
            wkri=wkri,
        )
        wkri._values = values
        return wkri

    @classmethod
    @lru_cache
    def _build_nodes(cls):
        if hasattr(cls.__bases__[0], "_build_nodes") and cls.proxy:
            return cls.__bases__[0]._build_nodes()

        if cls._nodes_real or cls._nodegroup_objects_real:
            raise RuntimeError(
                "Cache should never try and rebuild nodes when non-empty"
            )

        if LOAD_ALL_NODES:
            fltr = {"graph_id": cls.graphid}
        else:
            fltr = {
                "nodeid__in": [alias for alias in cls._wkrm.nodes]
            }
        nodes = {str(node.nodeid): node for node in Node.objects.filter(**fltr)}
        nodegroups = {
            str(nodegroup.nodegroupid): nodegroup
            for nodegroup in NodeGroup.objects.filter(
                nodegroupid__in=[node.nodegroup_id for node in nodes.values()]
            )
        }
        cls._nodes_real.update(nodes)
        cls._nodegroup_objects_real.update(nodegroups)
        cls._root_node = {
            "root": node for node in nodes.values() if node.nodegroup_id is None
        }.get("root")

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
            node.nodegroup_id
            for key, node in cls._nodes.items()
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
    def find(cls, resourceinstanceid, from_prefetch=None):
        """Find an individual well-known resource by instance ID."""

        resource = (
            from_prefetch(resourceinstanceid)
            if from_prefetch is not None
            else Resource.objects.get(pk=resourceinstanceid)
        )
        if resource:
            if str(resource.graph_id) != cls.graphid:
                raise RuntimeError(
                    f"Using find against wrong resource type: {resource.graph_id} for"
                    f" {cls.graphid}"
                )
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
        nodeid = str(wkfm._nodes()[key].nodeid)
        nodegroupid = str(wkfm._nodes()[key].nodegroup_id)
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
        nodeid = str(wkfm._nodes()[key].nodeid)
        nodegroupid = str(wkfm._nodes()[key].nodegroup_id)
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
        cls, node_objs, resource, related_prefetch=None, wkri=None
    ):
        """Populate fields from the ID-referenced Arches resource."""

        all_values = {}

        # load_tiles thins by user
        resource.tiles = TileProxyModel.objects.filter(resourceinstance=resource)

        implied_keys = {
            str(tile.nodegroup_id) for tile in resource.tiles if tile.data
        } - {
            str(nodeid) for tile in resource.tiles for nodeid in tile.data
        }
        implied_tiles = {}
        for tile in resource.tiles:
            if tile.data:
                for nodeid, node_value in tile.data.items():
                    if nodeid in node_objs:
                        key = node_objs[nodeid].alias

                        if node_value is not None:
                            all_values[key] = cls._make_pseudo_node_cls(
                                key, tile=tile, wkri=wkri
                            )
                            if str(tile.nodegroup_id) in implied_keys:
                                implied_tiles[str(tile.nodegroup_id)] = tile
        for nodeid, tile in implied_tiles.items():
            if nodeid in node_objs:
                key = node_objs[nodeid].alias
                all_values[key] = cls._make_pseudo_node_cls(
                    key, tile=tile, wkri=wkri
                )
        return all_values

    @classmethod
    def where(cls, cross_record=None, **kwargs):
        """Do a filtered query returning a list of well-known resources."""
        # TODO: replace with proper query
        unknown_keys = set(kwargs) - set(cls._nodes)
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

    def _make_pseudo_node(self, key, single=False, tile=None):
        return self._make_pseudo_node_cls(key, single=single, tile=tile, wkri=self)

    @classmethod
    def _make_pseudo_node_cls(cls, key, single=False, tile=None, wkri=None):
        node_obj = cls._node_objects_by_alias()[key]
        nodegroups = cls._nodegroup_objects()
        edges = cls._edges().get(str(node_obj.nodeid))
        value = None
        if node_obj.nodegroup_id and node_obj.is_collector and nodegroups[str(node_obj.nodegroup_id)].cardinality == "n" and not single:
            value = PseudoNodeList(
                node_obj,
                parent=wkri,
            )
        if value is None or tile:
            child_nodes = {}
            if edges is not None:
                child_nodes.update(
                    {
                        n.alias: (n, False)
                        for n in cls._node_objects().values()
                        if str(n.nodeid) in edges
                    }
                )
            child_nodes.update(
                {
                    n.alias: (n, True)
                    for n in cls._node_objects().values()
                    if n.nodegroup_id == node_obj.nodeid and n.nodeid != node_obj.nodeid
                }
            )
            node_value = PseudoNodeValue(
                tile=tile,
                node=node_obj,
                value=None,
                parent=wkri,
                child_nodes=child_nodes,
            )
            # If we have a tile in a list, add it
            if value is not None:
                value.append(node_value)
            else:
                value = node_value

        return value

    def __init_subclass__(cls, well_known_resource_model=None, proxy=None):
        super().__init_subclass__(well_known_resource_model=well_known_resource_model, proxy=proxy)
        if proxy is not None:
            cls.proxy = proxy
        if not cls.proxy:
            cls._nodes_real = {}
            cls._nodegroup_objects_real = {}
            cls._build_nodes()

    @classmethod
    def _add_events(cls):
        cls.post_save = Signal()

    def get_root(self):
        if self._root_node:
            if self._root_node.alias in self._values:
                value = self._values[self._root_node.alias]
            else:
                value = self._make_pseudo_node(
                    self._root_node.alias,
                )
                self._values[self._root_node.alias] = value
            return value

    def delete(self):
        """Delete the underlying resource."""
        return self.resource.delete()

    @classmethod
    def create(cls, _no_save=False, _do_index=True, **kwargs):
        # We have our own way of saving a resource in Arches.
        inst = super().create(_no_save=True, _do_index=_do_index, **kwargs)
        inst.to_resource(_no_save=_no_save, _do_index=_do_index)
        return inst

    @staticmethod
    def get_adapter():
        return ArchesDjangoAdapter()
