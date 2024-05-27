from typing import Any
import json
from arches.app.models.resource import Resource
from django.dispatch import Signal
from collections import UserDict
from functools import lru_cache
from datetime import datetime
from arches.app.models.models import ResourceXResource, Node, NodeGroup, Edge
from arches.app.models.graph import Graph
from arches.app.models.tile import Tile as TileProxyModel
from arches.app.models.system_settings import settings as system_settings
from arches.app.utils.permission_backend import get_nodegroups_by_perm
from contextvars import ContextVar
import logging
from arches.app.utils.permission_backend import (
    user_can_read_resource,
    user_can_edit_resource,
    user_can_delete_resource,
    user_can_read_graph
)
from arches_orm.datatypes import DataTypeNames

from arches_orm.wrapper import ResourceWrapper
from arches_orm.utils import snake
from arches_orm.errors import WKRIPermissionDenied, WKRMPermissionDenied, DescriptorsNotYetSet

from .bulk_create import BulkImportWKRM
from .pseudo_nodes import PseudoNodeList, PseudoNodeValue, PseudoNodeUnavailable
from .filters import SearchMixin

logger = logging.getLogger(__name__)


LOAD_FULL_NODE_OBJECTS = True
LOAD_ALL_NODES = True


def get_permitted_nodegroups(user):
    # To separate read and write, we need to know which tile nodes
    # have changed when saving (reliably).
    nodegroups = [str(ng) for ng in get_nodegroups_by_perm(user, "models.write_nodegroup")]
    return nodegroups

class ValueList(UserDict):
    def __init__(self, values, wrapper, related_prefetch):
        self._wrapper = wrapper
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
            if self._wrapper.resource:
                # Will KeyError if we do not have it.
                node = self._wrapper._nodes[key]
                ng = self._wrapper._ensure_nodegroup(
                    self._values,
                    node.nodegroup_id,
                    self._wrapper._node_objects(),
                    self._wrapper._nodegroup_objects(),
                    self._wrapper._edges(),
                    self._wrapper.resource,
                    related_prefetch=self._related_prefetch,
                    wkri=self._wrapper.view_model_inst,
                )
                self._values.update(ng)
            else:
                del self._values[key]
        if raise_error:
            return self.data[key]
        else:
            return self.data.get(key, default)

class ArchesDjangoResourceWrapper(SearchMixin, ResourceWrapper, proxy=True):
    _context: ContextVar[dict[str, Any] | None] | None = None
    _nodes_real: dict = None
    _nodegroup_objects_real: dict = None
    _root_node: Node | None = None
    _values_list: ValueList | None = None
    _values_real: list | None = None
    __datatype_factory = None

    """Provides functionality for translating to/from Arches types."""

    def _can_delete_resource(self, resource=None):
        if (user := self._context_get("user")):
            resource = resource or self.resource
            if resource and hasattr(resource, "resourceinstanceid"):
                resource = resource.resourceinstanceid
            return user_can_delete_resource(user, resource)
        # Context-free
        return True

    def _can_read_resource(self, resource=None):
        if (user := self._context_get("user")):
            resource = resource or self.resource
            if resource and hasattr(resource, "resourceinstanceid"):
                resource = resource.resourceinstanceid
            return user_can_read_resource(user, resource)
        # Context-free
        return True

    def _can_edit_resource(self, resource=None):
        if (user := self._context_get("user")):
            resource = resource or self.resource
            if resource and hasattr(resource, "resourceinstanceid"):
                resource = resource.resourceinstanceid
            return user_can_edit_resource(user, resource)
        # Context-free
        return True

    def to_string(self):
        try:
            name = self._name
        except NotImplementedError:
            name = super().to_string()
        return super().to_string() if name is None else name

    def _get_descriptor(self, descriptor, context=None):
        if context is None and (lang := self._context_get("language")):
            context = {
                "language": lang
            }
        if not self.resource:
            raise NotImplementedError()
        descriptor = self.resource.get_descriptor(descriptor, context)
        if descriptor is None:
            raise DescriptorsNotYetSet()
        return descriptor

    @property
    def _name(self):
        return self._get_descriptor("name")

    @property
    def _description(self):
        return self._get_descriptor("description")

    @property
    def _map_popup(self):
        return self._get_descriptor("name")

    @property
    def _values(self):
        if self._values_list is None:
            self._values_list = ValueList(
                self._values_real,
                wrapper=self,
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
                wrapper=self,
                related_prefetch=self._related_prefetch
            )

    def _update_tiles(
        self, tiles, all_values=None, nodegroup_id=None, root=None, parent=None, permitted_nodegroups: None | list[str]=None
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
                        tiles, root=pseudo_node, parent=parent, permitted_nodegroups=permitted_nodegroups
                    )
                    relationships += subrelationships
                if not isinstance(pseudo_node, PseudoNodeList):
                    t, r = pseudo_node.get_tile()
                    if t is not None and permitted_nodegroups is not None and (t.nodegroup_id is None or str(t.nodegroup_id) not in permitted_nodegroups):
                        # Warn if we can
                        if pseudo_node._original_tile and hasattr(pseudo_node._original_tile, "_original_data"):
                            if t.data == pseudo_node._original_tile._original_data:
                                continue
                        raise RuntimeError(f"Attempt to modify data that this user does not have permissions to: {t.nodegroup_id}")
                    else:
                        combined_tiles.append((t, r))
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

        if not _no_save and not self._can_edit_resource():
            raise WKRIPermissionDenied()

        resource = Resource(resourceinstanceid=self.id, graph_id=self.graphid)
        tiles = {}
        permitted_nodegroups = self._permitted_nodegroups()
        relationships = self._update_tiles(tiles, self._values, permitted_nodegroups=permitted_nodegroups)

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
            resource = Resource.objects.get(resourceinstanceid=self.id)
            self.resource = resource

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
    def _node_objects_by_alias(cls):
        if hasattr(cls.__bases__[0], "_node_objects_by_alias") and cls.proxy:
            return cls.__bases__[0]._node_objects_by_alias()

        return {node.alias: node for node in cls._node_objects().values()}

    @classmethod
    def _context_req(cls, key):
        return cls._context_get(cls, key, required=True)

    @classmethod
    def _context_get(cls, key, default=None, required=False):
        try:
            context = cls._context.get()
        except LookupError:
            logger.error("Need to set a context before using the ORM, or mark adapter context-free.")
            raise

        if context is None: # context-free, no restrictions
            if required:
                raise LookupError(f"Call cannot be done when context-free (needs {key})")
            return default
        if required and key not in context:
            raise LookupError(f"Context needs {key} for this call")
        return context.get(key, default)

    @classmethod
    def _can_read_graph(cls):
        try:
            context = cls._context.get()
        except LookupError:
            logger.error("Need to set a context before using the ORM, or mark adapter context-free.")
            raise

        if context is None: # Context-free, no restrictions
            return True

        context.setdefault("user_graphs", {})
        user = context.get("user")
        user_graphs = context["user_graphs"]

        # If set to False, rather than unset, then no.
        if (user_graph := user_graphs.get(str(cls))) is None:
            user_graph = bool(user_can_read_graph(user, str(cls.graphid)))
            user_graphs[str(cls)] = (
                {}
                if user_graph else
                False
            )
        elif user_graph is False:
            ...
        else:
            user_graph = True
        return user_graph

    @classmethod
    def _permitted_nodegroups(cls):
        if not cls ._can_read_graph():
            return []

        try:
            context = cls._context.get()
        except LookupError:
            logger.error("Need to set a context before using the ORM, or mark adapter context-free.")
            raise

        if context is None: # Context-free, no restrictions
            return list(cls._nodegroup_objects())

        if (permitted_nodegroups := context.get("user_graphs", {}).get(str(cls))):
            return permitted_nodegroups

        user = context.get("user")
        png = get_permitted_nodegroups(user)
        permitted_nodegroups = [
            key for key in cls._nodegroup_objects()
            if key in png
        ] + [None]
        context.setdefault("user_graphs", {})
        context["user_graphs"][str(cls)] = permitted_nodegroups
        return permitted_nodegroups

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

        if not cls ._can_read_graph():
            raise WKRMPermissionDenied()

        resource = Resource(resourceinstance.resourceinstanceid)
        return cls.from_resource(resource, cross_record=cross_record, lazy=lazy)

    def reload(self, ignore_prefetch=True, lazy=False):
        """Reload field values, but not node values for class."""

        if not self._can_read_graph():
            raise WKRMPermissionDenied()

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
            wkri=self.view_model_inst,
            lazy=lazy,
        )
        self._values = values
        return self

    @classmethod
    def from_resource(cls, resource, cross_record=None, related_prefetch=None, lazy=False):
        """Build a well-known resource from an Arches resource."""

        if not cls._can_read_graph():
            raise WKRMPermissionDenied()

        node_objs = cls._node_objects()
        wkri = cls.view_model(
            id=resource.resourceinstanceid,
            resource=resource,
            cross_record=cross_record,
            related_prefetch=related_prefetch,
        )
        if not wkri._._can_read_resource():
            raise WKRIPermissionDenied()
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
            wkri._,
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

    @property
    def __fields__(self):
        return self.get_fields()

    @classmethod
    @lru_cache
    def get_fields(cls, include_root=False):
        cls._build_nodes()
        def _fill_fields(pseudo_node):
            typ, multiple = pseudo_node.get_type()
            fields = {
                "type": DataTypeNames(typ),
                "node": pseudo_node,
                "multiple": multiple,
                "nodeid": str(pseudo_node.node.nodeid)
            }
            if (child_types := pseudo_node.get_child_types()):
                fields["children"] = {
                    child: _fill_fields(child_node) for child, child_node in child_types.items()
                }
            return fields

        root_fields = {}
        pseudo_node = cls._get_root_pseudo_node()
        if pseudo_node:
            root_fields.update(_fill_fields(pseudo_node))
        fields: dict[str, Any] = {}
        if not cls._remap_total or not cls._remap:
            root_fields.setdefault("children", fields)
            fields = root_fields["children"]

        if cls._remap and cls._model_remapping:
            for field, target in cls._model_remapping.items():
                if "." in target:
                    _, target = target.split(".", -1)
                logger.info("remapping: %s to %s", field, target)
                pseudo_node = cls._make_pseudo_node_cls(target, wkri=None)
                fields[snake(field)] = _fill_fields(pseudo_node)

        return {"": root_fields} if include_root else fields

    @classmethod
    def all_ids(cls):
        """Get IDs for all resources of this type."""

        if not cls ._can_read_graph():
            raise WKRMPermissionDenied()

        return list(
            Resource.objects.filter(graph_id=cls.graphid).values_list(
                "resourceinstanceid", flat=True
            )
        )

    @classmethod
    def all(cls, related_prefetch=None, lazy=False):
        """Get all resources of this type."""

        if not cls ._can_read_graph():
            raise WKRMPermissionDenied()

        resources = Resource.objects.filter(graph_id=cls.graphid).all()
        return [
            cls.from_resource(resource, related_prefetch=related_prefetch, lazy=lazy)
            for resource in resources
        ]

    @classmethod
    def find(cls, resourceinstanceid, from_prefetch=None, lazy=False):
        """Find an individual well-known resource by instance ID."""

        if not cls ._can_read_graph():
            raise WKRMPermissionDenied()

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

        if not self._can_edit_resource():
            raise WKRIPermissionDenied()

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

        if not self._can_edit_resource() and not _no_save:
            raise WKRIPermissionDenied()

        if not self._cross_record:
            raise NotImplementedError("This method is only implemented for relations")

        wkfm = self._cross_record["wkriFrom"]
        key = self._cross_record["wkriFromKey"]
        if not _no_save:
            wkfm.save()
            wkfm._.to_resource()
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

        if not cls ._can_read_graph():
            raise WKRMPermissionDenied()

        all_values = {
            node_objs[str(ng)].alias: False
            for ng, nodegroup in nodegroup_objs.items()
        }

        if not lazy:
            tiles = cls._get_allowed_tiles(resourceinstance=resource)
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
    def _get_allowed_tiles(
            cls,
            **kwargs
    ):
        permitted = cls._permitted_nodegroups()
        if "nodegroup_id" in kwargs:
            nodegroup_id = kwargs["nodegroup_id"]
            if nodegroup_id is None or nodegroup_id not in permitted:
                return []
        elif any(arg.startswith("nodegroup_id") for arg in kwargs):
            raise NotImplementedError(
                "Cannot currently filter for permitted nodegroups "
                "using non-identity nodegroup ID filters."
            )
        else:
            kwargs["nodegroup_id__in"] = permitted

        return TileProxyModel.objects.filter(**kwargs)

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
                nodegroup_tiles = cls._get_allowed_tiles(resourceinstance=resource, nodegroup_id=nodegroup_id)
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
    def first(cls, cross_record=None, lazy=False, case_i=False, **kwargs):
        if not cls ._can_read_graph():
            raise WKRMPermissionDenied()

        found = cls.where(cross_record=cross_record, lazy=lazy, case_i=case_i, **kwargs)
        if not found:
            raise RuntimeError(f"No results for search of {', '.join(kwargs.keys())}")
        return found[0]

    @classmethod
    def where(cls, cross_record=None, lazy=False, case_i=False, **kwargs):
        """Do a filtered query returning a list of well-known resources."""

        if not cls ._can_read_graph():
            raise WKRMPermissionDenied()

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

        # TODO: fix properly with Sqlite JSON
        contains_value: str | dict[str, Any] = {str(node.nodeid): value}
        if case_i:
            contains_key = "data__icontains"
            contains_value = json.dumps(contains_value)
        else:
            contains_key = "data__contains"

        filter_args = {
            "nodegroup_id": str(node.nodegroup_id),
            contains_key: contains_value
        }
        tiles = cls._get_allowed_tiles(**filter_args)
        return [
            cls.from_resource_instance(tile.resourceinstance, cross_record=cross_record, lazy=lazy)
            for tile in tiles
        ]

    @classmethod
    def _make_pseudo_node_cls(cls, key, single=False, tile=None, wkri=None):
        node_obj = cls._node_objects_by_alias()[key]
        nodegroups = cls._nodegroup_objects()

        permitted = cls._permitted_nodegroups()
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
                parent_cls=cls.view_model,
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
            if node_obj.nodegroup_id is not None and str(node_obj.nodegroup_id) not in permitted:
                node_value = PseudoNodeUnavailable(
                    node=node_obj,
                    parent=wkri,
                    parent_cls=cls.view_model,
                )
            else:
                node_value = PseudoNodeValue(
                    tile=tile,
                    node=node_obj,
                    value=None,
                    parent=wkri,
                    parent_cls=cls.view_model,
                    child_nodes=child_nodes,
                )
            # If we have a tile in a list, add it
            if value is not None:
                value.append(node_value)
            else:
                value = node_value

        return value

    def __init_subclass__(cls, well_known_resource_model=None, proxy=None, context=None):
        super().__init_subclass__(
            well_known_resource_model=well_known_resource_model, proxy=proxy, context=context
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
                    wkri=self.view_model_inst
                )
                self._values[self._root_node.alias] = [value]
            return value

    def delete(self):
        """Delete the underlying resource."""
        return self.resource.delete()

    @classmethod
    def create(cls, _no_save=False, _do_index=True, **kwargs):
        if not cls ._can_read_graph():
            raise WKRMPermissionDenied()

        # We have our own way of saving a resource in Arches.
        inst = super().create(_no_save=True, _do_index=_do_index, **kwargs)
        inst._.to_resource(_no_save=_no_save, _do_index=_do_index)
        return inst

    @classmethod
    def create_bulk(cls, fields: list, do_index: bool = True):
        if not cls ._can_read_graph():
            raise WKRMPermissionDenied()

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
