from arches.app.models.resource import Resource
from django.dispatch import Signal
from collections import UserDict
from functools import lru_cache
from datetime import datetime
from arches.app.models.models import ResourceXResource, Node, NodeGroup, Edge
from arches.app.models.graph import Graph
from arches.app.models.tile import Tile as TileProxyModel
from arches.app.models.system_settings import settings as system_settings
import logging
from arches_orm.datatypes import DataTypeNames

from arches_orm.wrapper import ResourceWrapper
from arches_orm.utils import snake

from .bulk_create import BulkImportWKRM
from .pseudo_nodes import PseudoNodeList, PseudoNodeValue

logger = logging.getLogger(__name__)


LOAD_FULL_NODE_OBJECTS = True
LOAD_ALL_NODES = True


class ValueList(UserDict):
    def __init__(self, values, wkri, related_prefetch):
        self._wkri = wkri
        self._related_prefetch = related_prefetch
        self._values = values

    @property
    def data(self):
        return {
            k: v for k, v in self._values.items() if v is not False
        }

    def setdefault(self, key, value):
        # Gives us a chance to lazy-load
        self._get(key, value, raise_error=False)
        self._values.setdefault(key, value)

    def __setitem__(self, key, value):
        self._values[key] = value

    def __getitem__(self, key):
        result = self._values[key]
        return self._get(key, default=result, raise_error=True)

    def _get(self, key, default=None, raise_error=False):
        result = self._values.get(key, default)
        if result is False:
            if self._wkri.resource:
                # Will KeyError if we do not have it.
                node = self._wkri._nodes[key]
                ng = self._wkri._ensure_nodegroup(
                    self._values,
                    node.nodegroup_id,
                    self._wkri._node_objects(),
                    self._wkri._nodegroup_objects(),
                    self._wkri._edges(),
                    self._wkri.resource,
                    related_prefetch=self._related_prefetch,
                    wkri=self._wkri,
                )
                self._values.update(ng)
            else:
                del self._values[key]
        if raise_error:
            return self.data[key]
        else:
            return self.data.get(key, default)

class ArchesDjangoResourceWrapper(ResourceWrapper, proxy=True):
    _nodes_real: dict = None
    _nodegroup_objects_real: dict = None
    _root_node: Node | None = None
    _values_list: ValueList | None = None
    _values_real: list | None = None
    __datatype_factory = None

    """Provides functionality for translating to/from Arches types."""

    @property
    def _values(self):
        if self._values_list is None:
            self._values_list = ValueList(
                self._values_real,
                self,
                related_prefetch=self._related_prefetch
            )
        return self._values_list

    @_values.setter
    def _values(self, values: dict | ValueList):
        if isinstance(values, ValueList):
            self._values_list = values
        else:
            self._values_list = ValueList(
                values,
                self,
                related_prefetch=self._related_prefetch
            )

    def _update_tiles(
        self, tiles, all_values=None, nodegroup_id=None, root=None, parent=None
    ):
        if not root:
            if not all_values:
                return []
            root = [
                nodelist[0]
                for nodelist in all_values.values()
                if nodelist[0].node.nodegroup_id is None
            ][0]

        combined_tiles = []
        relationships = []
        if not isinstance(root, PseudoNodeList):
            parent = root
        for pseudo_node in root.get_children():
            if isinstance(pseudo_node, PseudoNodeList) or pseudo_node.accessed:
                if len(pseudo_node):
                    subrelationships = self._update_tiles(
                        tiles, root=pseudo_node, parent=parent
                    )
                    relationships += subrelationships
                if not isinstance(pseudo_node, PseudoNodeList):
                    t_and_r = pseudo_node.get_tile()
                    combined_tiles.append(t_and_r)
            # This avoids loading a tile as a set of view models, simply to re-save it.
            elif not isinstance(pseudo_node, PseudoNodeList) and pseudo_node._original_tile:
                # TODO: NOTE THAT THIS DOES NOT CAPTURE RELATIONSHIPS THAT HAVE NOT BEEN ACCESSED
                combined_tiles.append((
                    pseudo_node._original_tile,
                    []
                ))

        for tile, subrelationships in combined_tiles:
            if tile:
                if parent and parent.tile != tile and parent.node.nodegroup_id:
                    tile.parenttile = parent.tile
                nodegroup_id = str(tile.nodegroup_id)
                tiles.setdefault(nodegroup_id, [])
                relationships += [
                    (len(tiles[nodegroup_id]), *relationship)
                    for relationship in subrelationships
                ]
                tiles[nodegroup_id].append(tile)
        return relationships

    def to_resource(
        self,
        verbose=False,
        strict=False,
        _no_save=False,
        _known_new=False,
        _do_index=True,
        save_related_if_missing=True,
    ):
        """Construct an Arches resource.

        This may be new or existing, for this well-known resource.
        """

        resource = Resource(resourceinstanceid=self.id, graph_id=self.graphid)
        tiles = {}
        relationships = self._update_tiles(tiles, self._values)

        # parented tiles are saved hierarchically
        resource.tiles = [t for t in sum((ts for ts in tiles.values()), [])]

        if not resource.createdtime:
            resource.createdtime = datetime.now()
        # errors = resource.validate(verbose=verbose, strict=strict)
        # if len(errors):
        #    raise RuntimeError(str(errors))

        # FIXME: potential consequences for thread-safety
        # This is required to avoid e.g. missing related models preventing
        # saving (as we cannot import those via CSV on first step)
        self._pending_relationships = []
        do_final_save = False
        if not _no_save:
            if (
                self.id
                and resource.resourceinstanceid
                and self.id == resource.resourceinstanceid
            ):
                do_final_save = True
            else:
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

        # Don't think we actually need this if the resource gets saved, as postsave RI
        # datatype handles it. We do for sqlite at the very least, and likely gathering
        # for bulk.
        _no_save = _no_save or not (self.get_adapter().config.get("save_crosses", False))
        # TODO: fix expectation of one cross per tile

        crosses = {}
        for cross in ResourceXResource.objects.filter(
            resourceinstanceidfrom=resource
        ):
            crosses.setdefault(str(cross.tileid), [])
            crosses[str(cross.tileid)].append(cross)
        for tile_ix, nodegroup_id, nodeid, related in relationships:
            value = tiles[nodegroup_id][tile_ix].data[nodeid]
            tileid = str(tiles[nodegroup_id][tile_ix].tileid)
            if not related.id:
                if save_related_if_missing:
                    related.save()
                else:
                    logger.warning("Not saving a related model as not requested")
                    continue
            need_cross = tileid not in crosses
            cross_resourcexid = None
            if tileid in crosses:
                for cross in crosses[tileid]:
                    if (
                        str(cross.resourceinstanceidto_id) == str(related.id) and
                        str(cross.resourceinstanceidfrom_id) == str(resource.id)
                    ):
                        need_cross = False
                        cross_resourcexid = str(cross.resourcexid)
            if need_cross:
                cross = ResourceXResource(
                    resourceinstanceidfrom=resource,
                    resourceinstanceidto_id=related.id,
                )
                if _no_save:
                    self._pending_relationships.append((value, related, self))
                else:
                    cross.save()
                    cross_resourcexid = str(cross.resourcexid)

            cross_value = {
                "resourceId": str(cross.resourceinstanceidto_id),
                "ontologyProperty": "",
                "resourceXresourceId": cross_resourcexid,
                "inverseOntologyProperty": "",
            }
            if isinstance(value, list):
                if not any(
                    (entry["resourceId"] == cross_value["resourceId"]) or
                    (
                        entry["resourceXresourceId"] is not None and
                        entry["resourceXresourceId"] == cross_value["resourceXresourceId"]
                    )
                    for entry in value
                ):
                    value.append(cross_value)
            else:
                value.update(cross_value)
            do_final_save = True
        if do_final_save:
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
    def _node_datatypes(cls):
        return {
            str(nodeid): node.datatype for nodeid, node in cls._node_objects().items()
        }

    @classmethod
    @lru_cache
    def _graph(cls):
        return Graph.objects.get(graphid=cls.graphid)

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
    def from_resource_instance(cls, resourceinstance, cross_record=None, lazy=False):
        """Build a well-known resource from a resource instance."""
        resource = Resource(resourceinstance.resourceinstanceid)
        return cls.from_resource(resource, cross_record=cross_record, lazy=lazy)

    def reload(self, ignore_prefetch=True, lazy=False):
        """Reload field values, but not node values for class."""
        if not self.id:
            raise RuntimeError("Cannot reload without a database ID")

        resource = (
            self._related_prefetch(self.id)
            if not ignore_prefetch and self._related_prefetch is not None
            else Resource.objects.get(pk=self.id)
        )
        if not resource:
            raise RuntimeError(f"Could not retrieve resource with ID {self.id}")

        if str(resource.graph_id) != self.graphid:
            raise RuntimeError(
                f"Using find against wrong resource type: {resource.graph_id} for"
                f" {self.graphid}"
            )
        node_objs = self._node_objects()
        nodegroup_objs = self._nodegroup_objects()
        edges = self._edges()
        self._values = {}
        values = self.values_from_resource(
            node_objs,
            nodegroup_objs,
            edges,
            resource,
            related_prefetch=self._related_prefetch,
            wkri=self,
            lazy=lazy,
        )
        self._values = values
        return self

    @classmethod
    def from_resource(cls, resource, cross_record=None, related_prefetch=None, lazy=False):
        """Build a well-known resource from an Arches resource."""

        node_objs = cls._node_objects()
        wkri = cls(
            id=resource.resourceinstanceid,
            resource=resource,
            cross_record=cross_record,
            related_prefetch=related_prefetch,
        )
        nodegroup_objs = cls._nodegroup_objects()
        edges = cls._edges()
        values = cls.values_from_resource(
            node_objs,
            nodegroup_objs,
            edges,
            resource,
            related_prefetch=related_prefetch,
            wkri=wkri,
            lazy=lazy,
        )
        wkri._values = ValueList(
            values,
            wkri,
            related_prefetch=related_prefetch
        )
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
            fltr = {"nodeid__in": [alias for alias in cls._wkrm.nodes]}
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
    @property
    def __fields__(cls):
        cls._build_nodes()
        def _fill_fields(pseudo_node):
            typ, multiple = pseudo_node.get_type()
            fields = {
                "type": DataTypeNames(typ),
                "multiple": multiple,
                "nodeid": str(pseudo_node.node.nodeid)
            }
            if (child_types := pseudo_node.get_child_types()):
                fields["children"] = {
                    child: _fill_fields(child_node) for child, child_node in child_types.items()
                }
            return fields

        if cls._remap and cls._model_remapping:
            fields = {}
            for field, target in cls._model_remapping.items():
                _, target = target.split(".", -1)
                pseudo_node = cls._make_pseudo_node_cls(target, wkri=None)
                fields[snake(field)] = _fill_fields(pseudo_node)
            return fields
        else:
            pseudo_node = cls._get_root_pseudo_node()
            if pseudo_node:
                return _fill_fields(pseudo_node).get("children")
        return {}

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
            str(node.nodegroup_id)
            for key, node in cls._node_objects_by_alias().items()
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
    def all(cls, related_prefetch=None, lazy=False):
        """Get all resources of this type."""

        resources = Resource.objects.filter(graph_id=cls.graphid).all()
        return [
            cls.from_resource(resource, related_prefetch=related_prefetch, lazy=lazy)
            for resource in resources
        ]

    @classmethod
    def find(cls, resourceinstanceid, from_prefetch=None, lazy=False):
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
            return cls.from_resource(resource, lazy=lazy)
        return None

    def remove(self):
        """When called via a relationship (dot), remove the relationship."""

        if not self._cross_record:
            raise NotImplementedError("This method is only implemented for relations")

        from arches_orm.view_models.resources import RelatedResourceInstanceViewModelMixin, RelatedResourceInstanceListViewModel

        wkfm = self._cross_record["wkriFrom"]
        key = self._cross_record["wkriFromKey"]
        pseudo_node_list = wkfm._values[key]
        if not isinstance(pseudo_node_list, PseudoNodeList) and not isinstance(pseudo_node_list, list):
            pseudo_node_list = [pseudo_node_list]

        for pseudo_node in pseudo_node_list:
            if isinstance(pseudo_node.value, RelatedResourceInstanceListViewModel):
                pseudo_node.value.remove(self)
            elif isinstance(pseudo_node.value, RelatedResourceInstanceViewModelMixin):
                # if str(pseudo_node.value.resourceinstanceid) != str(self.id):
                #     raise RuntimeError(
                #         f"Mix-up when removing a related resource for {key} of {wkfm.id},"
                #         f" which should be {self.id} but is {pseudo_node.value.resourceinstanceid}"
                #     )
                if str(pseudo_node.value.resourceinstanceid) == str(self.id):
                    pseudo_node.clear()
            # else:
            #     raise RuntimeError(
            #         f"Mix-up when removing a related resource for {key} of {wkfm.id},"
            #         f" which should be a related resource, but is {type(pseudo_node.value)}"
            #     )
        wkfm.save()

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
                value = (tile.data or {}).get(nodeid, [])
                value.append(
                    {
                        "resourceId": str(self.resource.resourceinstanceid),
                        "ontologyProperty": "",
                        "resourceXresourceId": str(cross.resourcexid),
                        "inverseOntologyProperty": "",
                    }
                )
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
        cls,
        node_objs,
        nodegroup_objs,
        edges,
        resource,
        related_prefetch=None,
        wkri=None,
        lazy=False,
    ):
        """Populate fields from the ID-referenced Arches resource."""

        all_values = {
            node_objs[str(ng)].alias: False
            for ng, nodegroup in nodegroup_objs.items()
        }

        if not lazy:
            tiles = TileProxyModel.objects.filter(resourceinstance=resource)
            for ng, nodegroup in nodegroup_objs.items():
                all_values.update(
                    cls._ensure_nodegroup(
                        all_values,
                        ng,
                        node_objs,
                        nodegroup_objs,
                        edges,
                        resource,
                        related_prefetch=related_prefetch,
                        wkri=wkri,
                        tiles=tiles
                    )
                )
        return all_values

    @classmethod
    def _ensure_nodegroup(
        cls,
        all_values,
        nodegroup_id,
        node_objs,
        nodegroup_objs,
        edges,
        resource,
        related_prefetch=None,
        wkri=None,
        add_if_missing=False,
        tiles=None,
    ):
        nodegroup_id = str(nodegroup_id)
        node = node_objs[nodegroup_id]
        implied_nodegroups = set()
        value = all_values.get(node.alias, None)
        if value is False or (add_if_missing and value is None):
            if node.alias in all_values:
                del all_values[node.alias]
            if tiles is None:
                nodegroup_tiles = TileProxyModel.objects.filter(resourceinstance=resource, nodegroup_id=nodegroup_id)
            else:
                nodegroup_tiles = [tile for tile in tiles if str(tile.nodegroup_id) == nodegroup_id]
            if not nodegroup_tiles and add_if_missing:
                nodegroup_tiles = [None]
            new_values, new_implied_nodegroups = cls._values_from_resource_nodegroup(
                all_values,
                nodegroup_tiles,
                nodegroup_id,
                node_objs,
                nodegroup_objs,
                edges,
                resource,
                related_prefetch=related_prefetch,
                wkri=wkri,
            )
            all_values.update(new_values)
            implied_nodegroups |= new_implied_nodegroups

        while implied_nodegroups:
            seen_nodegroups = set(implied_nodegroups)
            for nodegroup_id in seen_nodegroups:
                all_values = cls._ensure_nodegroup(
                    all_values,
                    nodegroup_id,
                    node_objs,
                    nodegroup_objs,
                    edges,
                    resource,
                    related_prefetch=related_prefetch,
                    wkri=wkri,
                    add_if_missing=True,
                )
            implied_nodegroups -= seen_nodegroups

        return all_values

    @classmethod
    def _values_from_resource_nodegroup(
        cls,
        existing_values,
        nodegroup_tiles,
        nodegroup_id,
        node_objs,
        nodegroup_objs,
        edges,
        resource,
        related_prefetch=None,
        wkri=None,
    ):
        """Populate fields from the ID-referenced Arches resource."""
        all_values = {}

        implied_nodegroups = set()

        def _add_node(node: Node, tile: TileProxyModel | None) -> None:
            key = node.alias
            if existing_values.get(key, False) is not False:
                raise RuntimeError(f"Tried to load node twice: {key}")
            all_values.setdefault(key, [])
            pseudo_node = cls._make_pseudo_node_cls(key, tile=tile, wkri=wkri)
            # We shouldn't have to take care of this case, as it should already
            # be included below.
            # if tile.parenttile_id:
            for domain, ranges in edges.items():
                if str(node.nodegroup_id) in ranges:
                    implied_nodegroups.add(
                        str(node_objs[domain].nodegroup_id)
                        if node_objs[domain].nodegroup_id
                        else str(node_objs[domain].nodeid)  # for root
                    )
                    break
            if isinstance(pseudo_node, PseudoNodeList):
                if all_values.get(key, False) is not False:
                    for pseudo_node_list in all_values[key]:
                        if not isinstance(pseudo_node_list, PseudoNodeList):
                            raise RuntimeError("Should be all lists")
                        if pseudo_node_list._parent_node == pseudo_node._parent_node:
                            for ps in pseudo_node:
                                # FIXME: do we need to deal with _parent_node?
                                pseudo_node_list.append(ps)
                            return
            all_values[key].append(pseudo_node)

        for tile in nodegroup_tiles:
            parent_node = node_objs[nodegroup_id]
            _add_node(parent_node, tile)

            if tile:
                tile_nodes = dict(tile.data.items())
                tile_nodes.setdefault(tile.nodegroup_id, {})
                for nodeid, node_value in tile_nodes.items():
                    nodeid = str(nodeid)
                    if nodeid == nodegroup_id:
                        continue
                    node = node_objs[nodeid]
                    if node_value is not None:
                        _add_node(node, tile)
        return all_values, implied_nodegroups

    @classmethod
    def where(cls, cross_record=None, lazy=False, **kwargs):
        """Do a filtered query returning a list of well-known resources."""
        # TODO: replace with proper query
        unknown_keys = set(kwargs) - set(cls._node_objects_by_alias())
        if unknown_keys:
            raise KeyError(f"Unknown key(s) {unknown_keys}")

        if len(kwargs) != 1:
            raise NotImplementedError("Need exactly one filter")

        key = list(kwargs)[0]
        value = kwargs[key]

        node = cls._node_objects_by_alias().get(key)
        if not node:
            raise RuntimeError(
                f"This key {key} is not known on this model {cls.__name__}"
            )
        tiles = TileProxyModel.objects.filter(
            nodegroup_id=str(node.nodegroup_id),
            data__contains={str(node.nodeid): value},
        )
        return [
            cls.from_resource_instance(tile.resourceinstance, cross_record=cross_record, lazy=lazy)
            for tile in tiles
        ]

    @classmethod
    def _make_pseudo_node_cls(cls, key, single=False, tile=None, wkri=None):
        node_obj = cls._node_objects_by_alias()[key]
        nodegroups = cls._nodegroup_objects()
        edges = cls._edges().get(str(node_obj.nodeid))
        value = None
        if (
            node_obj.nodegroup_id
            and node_obj.is_collector
            and nodegroups[str(node_obj.nodegroup_id)].cardinality == "n"
            and not single
        ):
            value = PseudoNodeList(
                node_obj,
                parent=wkri,
                parent_cls=cls,
            )
        if value is None or tile:
            child_nodes = {}
            if edges is not None:
                child_nodes.update(
                    {
                        n.alias: (n, not n.is_collector)
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
                parent_cls=cls,
                child_nodes=child_nodes,
            )
            # If we have a tile in a list, add it
            if value is not None:
                value.append(node_value)
            else:
                value = node_value

        return value

    def __init_subclass__(cls, well_known_resource_model=None, proxy=None):
        super().__init_subclass__(
            well_known_resource_model=well_known_resource_model, proxy=proxy
        )
        if proxy is not None:
            cls.proxy = proxy
        if not cls.proxy:
            # We should not actually fail without a graph...
            cls._nodes_real = {}
            cls._nodegroup_objects_real = {}
            cls._build_nodes()

    @classmethod
    def _add_events(cls):
        cls.post_save = Signal()
        cls.post_related_to = Signal()
        cls.post_related_from = Signal()

    @classmethod
    def _get_root_pseudo_node(cls):
        if cls._root_node:
            return cls._make_pseudo_node_cls(
                cls._root_node.alias,
                wkri=None
            )
        return None

    def get_root(self):
        if self._root_node:
            self._values.setdefault(self._root_node.alias, [])
            if len(self._values[self._root_node.alias]) not in (0, 1):
                raise RuntimeError("Cannot have multiple root tiles")
            if self._values[self._root_node.alias]:
                value = self._values[self._root_node.alias][0]
            else:
                value = self._make_pseudo_node_cls(
                    self._root_node.alias,
                    wkri=self
                )
                self._values[self._root_node.alias] = [value]
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

    @classmethod
    def create_bulk(cls, fields: list, do_index: bool = True):
        requested_wkrms = []
        for n, field_set in enumerate(fields):
            try:
                if n % 10 == 0:
                    logger.info(f"create_bulk: {n} / {len(fields)}")
                requested_wkrms.append(cls.create(_no_save=True, _do_index=do_index, **field_set))
            except Exception:
                logger.error(f"Failed item {n}")
                raise
        bulk_etl = BulkImportWKRM()
        return bulk_etl.write(requested_wkrms, do_index=do_index)

    @staticmethod
    def get_adapter():
        from arches_orm import adapter

        return adapter.get_adapter(key="arches-django")
