import logging
from typing import Literal, Any
from collections import UserDict
from functools import lru_cache
from dataclasses import dataclass
from threading import Event
from arches_orm.wrapper import ResourceWrapper
from arches_orm.pseudo_node.pseudo_nodes import PseudoNodeList, PseudoNodeValue, PseudoNodeUnavailable
from .datatypes._register import get_view_model_for_datatype
from .datatypes.resource_models import StaticNodeGroup, StaticNode, retrieve_graph
from .datatypes.resource_instances import StaticTile, STATIC_STORE


logger = logging.getLogger(__name__)

LOAD_ALL_NODES = True

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


class StaticResourceWrapper(ResourceWrapper, proxy=True):
    """Static wrapper for all well-known resources.

    When you use, `Person`, etc. it will be this class in disguise.
    """

    _nodes_real: dict = None
    _edges_real: dict = None
    _nodegroup_objects_real: dict = None

    @classmethod
    def search(cls, text, fields=None, _total=None) -> tuple[list[int], int]:
        """Search for resources of this model, and return as well-known resources."""
        results = []
        return results, len(results)

    @classmethod
    def all_ids(cls) -> list[str]:
        """Get IDs for all resources of this type."""
        return [
            resource.id for resource in cls.all()
        ]

    @classmethod
    def all(cls, related_prefetch=None) -> list["StaticResourceWrapper"]:
        """Get all resources of this type."""
        STATIC_STORE.load_all()
        return [
            cls.from_static_resource(resource)
            for id, resource in STATIC_STORE.items()
            if resource.resourceinstance.graph_id == cls._wkrm.graphid
        ]

    @classmethod
    def find(cls, resourceinstanceid):
        """Find an individual well-known resource by instance ID."""
        return STATIC_STORE[resourceinstanceid]

    @classmethod
    def delete(self):
        """Delete the underlying resource."""
        del STATIC_STORE[self.id]

    @classmethod
    def remove(self):
        """When called via a relationship (dot), remove the relationship."""

    @classmethod
    def append(self, _no_save=False):
        """When called via a relationship (dot), append to the relationship."""

    def reload(self, ignore_prefetch=True):
        """Reload field values, but not node values for class."""

    def get_root(self):
        """Get the root value."""

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
        if not self.resource or descriptor != "name":
            raise NotImplementedError()
        descriptor = self.resource.resourceinstance.name
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
                return [], set()
            root = [
                nodelist[0]
                for nodelist in all_values.values()
                if nodelist[0].node.nodegroup_id is None
            ][0]

        combined_tiles = []
        relationships = []
        ghost_tiles = set()
        if not isinstance(root, PseudoNodeList):
            parent = root
        for pseudo_node in root.get_children():
            if isinstance(pseudo_node.value, RelatedResourceInstanceViewModelMixin):
                # Do not cross between resources. The relationship should
                # be captured. The canonical example of this is a semantic node that
                # gives us a related resource instance.
                t, r = pseudo_node.get_tile()
                combined_tiles.append((t, r))
                continue
            if isinstance(pseudo_node, PseudoNodeList) or pseudo_node.accessed:
                if len(pseudo_node):
                    subrelationships, subghost_tiles = self._update_tiles(
                        tiles, root=pseudo_node, parent=parent, permitted_nodegroups=permitted_nodegroups
                    )
                    relationships += subrelationships
                    ghost_tiles |= subghost_tiles
                if isinstance(pseudo_node, PseudoNodeList):
                    # Only hold ghost tiles that have been saved.
                    ghost_tiles = {
                        tile for ghost in pseudo_node.free_ghost_children()
                        if (tile := ghost.get_tile()[0]) and tile.pk and not tile._state.adding
                    }
                else:
                    t, r = pseudo_node.get_tile()
                    if t is not None and permitted_nodegroups is not None and (t.nodegroup_id is None or t.nodegroup_id not in permitted_nodegroups):
                        # Warn if we can
                        if pseudo_node._original_tile and hasattr(pseudo_node._original_tile, "_original_data"):
                            if t.data == pseudo_node._original_tile._original_data:
                                continue
                        raise RuntimeError(f"Attempt to modify data that this user does not have permissions to: {t.nodegroup_id} in {self}")
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
                nodegroup_id = tile.nodegroup_id
                tiles.setdefault(nodegroup_id, [])
                relationships += [
                    (len(tiles[nodegroup_id]), *relationship)
                    for relationship in subrelationships
                ]
                tiles[nodegroup_id].append(tile)
        return relationships, ghost_tiles

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
        return True

    @classmethod
    @lru_cache
    def _node_objects(cls):
        """Caching retrieval of all Arches nodes for this model."""

        if hasattr(cls.__bases__[0], "_node_objects") and cls.proxy:
            return cls.__bases__[0]._node_objects()

        cls._build_nodes()
        return cls._nodes_real

    @classmethod
    @lru_cache
    def _node_datatypes(cls):
        return {
            nodeid: node.datatype for nodeid, node in cls._node_objects().items()
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

        cls._build_nodes()
        return cls._edges_real

    @classmethod
    @lru_cache
    def _nodegroup_objects(cls) -> dict[str, StaticNodeGroup]:
        """Caching retrieval of all Arches nodegroups for this model."""

        if hasattr(cls.__bases__[0], "_nodegroup_objects") and cls.proxy:
            return cls.__bases__[0]._nodegroup_objects()

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

        if resource.graph_id != self.graphid:
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
    @lru_cache
    def _build_nodes(cls):
        if hasattr(cls.__bases__[0], "_build_nodes") and cls.proxy:
            return cls.__bases__[0]._build_nodes()

        if cls._nodes_real or cls._nodegroup_objects_real:
            raise RuntimeError(
                "Cache should never try and rebuild nodes when non-empty"
            )

        graph = retrieve_graph(cls._wkrm.graphid)
        nodes = {node.nodeid: node for node in graph.nodes}
        if not LOAD_ALL_NODES:
            nodes = {key: node for key, node in nodes.items() if key in cls._wkrm.nodes}

        needed_nodegroups = [node.nodegroup_id for node in nodes.values()]
        nodegroups = {
            nodegroup.nodegroupid: nodegroup
            for nodegroup in graph.nodegroups
            if nodegroup.nodegroupid in needed_nodegroups
        }
        edge_pairs = [
            (edge.domainnode_id, edge.rangenode_id)
            for edge in graph.edges
        ]
        edges = {}
        for domain, rang in edge_pairs:
            edges.setdefault(domain, [])
            edges[domain].append(rang)

        cls._nodes_real.update(nodes)
        cls._nodegroup_objects_real.update(nodegroups)
        cls._edges_real.update(edges)

    @classmethod
    def all_fields(cls):
        root_fields = cls.get_fields()
        fields = {}
        def _add_children(children):
            for name, child in children.items():
                fields[name] = dict(child)
                grandchildren = fields[name].get("children", {})
                if grandchildren:
                    _add_children(grandchildren)
                    del fields[name]["children"]
        _add_children(root_fields)
        return fields

    @classmethod
    @lru_cache
    def get_fields(cls, include_root=False):
        cls._build_nodes()
        def _fill_fields(pseudo_node):
            typ, multiple = pseudo_node.get_type()
            try:
                typ = DataTypeNames(typ)
            except ValueError:
                logger.error(r"Could not load %s for %s", typ, str(cls))
                return None
            fields = {
                "type": typ,
                "node": pseudo_node,
                "multiple": multiple,
                "nodeid": pseudo_node.node.nodeid
            }
            if (child_types := pseudo_node.get_child_types()):
                fields["children"] = {
                    child: _fields for child, child_node in child_types.items()
                    if (_fields := _fill_fields(child_node))
                }
            return fields

        root_fields = {}
        pseudo_node = cls._get_root_pseudo_node()
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
    def _permitted_nodegroups(cls):
        return list(cls._nodegroup_objects())

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

        nodes = cls._node_objects()
        if nodegroups := kwargs.get("nodegroup_id__in", []):
            nodes = [node for node in nodes if node.nodegroup_id in nodegroups]
            del kwargs["nodegroup_id__in"]
        if nodegroup := kwargs.get("nodegroup_id", []):
            nodes = [node for node in nodes if node.nodegroup_id == nodegroup]
            del kwargs["nodegroup_id"]
        if resourceinstance := kwargs.get("resourceinstance", []):
            resourceid = resourceinstance.resource_id
            del kwargs["resourceinstance"]
        else:
            resourceid = None

        if kwargs:
            raise NotImplementedError(f"Cannot search for {kwargs}")

        tiles = []
        for nodeid in nodes:
            for resource_id, tile_id in STATIC_STORE.search_by_nodeid(nodeid=nodeid, resourceid=resourceid):
                resource = STATIC_STORE.get(resource_id)
                if resource is None:
                    raise RuntimeError(f"Cache expecting {resource_id} to exist but it is missing.")
                tile = [tile for tile in resource.tiles if tile.tileid == tile_id][0]
                tiles.append(tile)

        return tiles

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
        node = node_objs[nodegroup_id]
        implied_nodegroups = set()
        value = all_values.get(node.alias, None)
        if value is False or (add_if_missing and value is None):
            if node.alias in all_values:
                del all_values[node.alias]
            if tiles is None:
                nodegroup_tiles = cls._get_allowed_tiles(resourceinstance=resource, nodegroup_id=nodegroup_id)
            else:
                nodegroup_tiles = [tile for tile in tiles if tile.nodegroup_id == nodegroup_id]
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
            node_objs[ng].alias: False
            for ng, nodegroup in nodegroup_objs.items()
        }

        if not lazy:
            tiles = resource.tiles
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

        def _add_node(node: StaticNode, tile: StaticTile | None) -> None:
            key = node.alias
            if existing_values.get(key, False) is not False:
                raise RuntimeError(f"Tried to load node twice: {key}")
            all_values.setdefault(key, [])
            pseudo_node = cls._make_pseudo_node_cls(key, tile=tile, wkri=wkri)
            # We shouldn't have to take care of this case, as it should already
            # be included below.
            # if tile.parenttile_id:
            for domain, ranges in edges.items():
                if node.nodegroup_id in ranges:
                    implied_nodegroups.add(
                        node_objs[domain].nodegroup_id
                        if node_objs[domain].nodegroup_id
                        else node_objs[domain].nodeid  # for root
                    )
                    break
            if isinstance(pseudo_node, PseudoNodeList):
                if all_values.get(key, False) is not False:
                    for pseudo_node_list in all_values[key]:
                        if not isinstance(pseudo_node_list, PseudoNodeList):
                            raise RuntimeError(f"Should be all lists not {type(pseudo_node_list)}")
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
                    if nodeid == nodegroup_id:
                        continue
                    node = node_objs[nodeid]
                    if node_value is not None:
                        _add_node(node, tile)
        return all_values, implied_nodegroups

    @classmethod
    def first(cls, cross_record=None, lazy=False, case_i=False, **kwargs):
        found = cls.where(cross_record=cross_record, lazy=lazy, case_i=case_i, **kwargs)
        if not found:
            raise RuntimeError(f"No results for search of {', '.join(kwargs.keys())}")
        return found[0]

    @classmethod
    def where(cls, cross_record=None, lazy=False, case_i=False, **kwargs):
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

        resource_tiles = STATIC_STORE.search_by_nodeid(node.nodeid, None, str(value), case_i=case_i)
        resources = set()
        for resource_id, _ in resource_tiles:
            if resource_id in resources:
                continue
            resources.add(resource_id)
            yield cls.from_static_resource(STATIC_STORE[resource_id], cross_record=cross_record, lazy=lazy)

    @classmethod
    def from_static_resource(cls, resource, cross_record=None, related_prefetch=None, lazy=False):
        """Build a well-known resource from an Arches resource."""

        node_objs = cls._node_objects()
        wkri = cls.view_model(
            id=resource.resourceinstance.resourceinstanceid,
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
            wkri._,
            related_prefetch=related_prefetch
        )
        return wkri

    @classmethod
    def _make_pseudo_node_cls(cls, key, single=False, tile=None, wkri=None):
        node_obj = cls._node_objects_by_alias()[key]
        nodegroups = cls._nodegroup_objects()

        permitted = cls._permitted_nodegroups()
        edges = cls._edges().get(node_obj.nodeid)
        value = None
        if (
            node_obj.nodegroup_id
            and node_obj.is_collector
            and nodegroups[node_obj.nodegroup_id].cardinality == "n"
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
                        if n.nodeid in edges
                    }
                )
            if node_obj.nodegroup_id is not None and node_obj.nodegroup_id not in permitted:
                node_value = PseudoNodeUnavailable(
                    node=node_obj,
                    parent=wkri,
                    parent_cls=cls.view_model,
                )
            else:
                node_value = PseudoNodeValue(
                    tile=tile,
                    TileProxyModel=StaticTile.model_construct,
                    get_view_model_for_datatype=get_view_model_for_datatype,
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
            cls._edges_real = {}
            cls._nodegroup_objects_real = {}

    @classmethod
    def _add_events(cls):
        cls.post_save = Event()
        cls.post_related_to = Event()
        cls.post_related_from = Event()

    @classmethod
    @lru_cache
    def _root_node(cls) -> StaticNode:
        nodes = cls._node_objects()
        root_node = {
            "root": node for node in nodes.values() if node.nodegroup_id is None
        }.get("root")
        if not root_node:
            logger.error("COULD NOT FIND ROOT NODE FOR %s. Does the graph %s still exist?", cls, cls.graphid)
        return root_node

    @classmethod
    def _get_root_pseudo_node(cls):
        if (node := cls._root_node()):
            return cls._make_pseudo_node_cls(
                node.alias,
                wkri=None
            )
        return None

    def get_root(self):
        if (node := self._root_node()):
            self._values.setdefault(node.alias, [])
            if len(self._values[node.alias]) not in (0, 1):
                raise RuntimeError("Cannot have multiple root tiles")
            if self._values[node.alias]:
                value = self._values[node.alias][0]
            else:
                value = self._make_pseudo_node_cls(
                    node.alias,
                    wkri=self.view_model_inst
                )
                self._values[node.alias] = [value]
            return value

    def delete(self):
        """Delete the underlying resource."""
        return self.resource.delete()

    @classmethod
    def create(cls, _no_save=False, _do_index=True, **kwargs):
        # We have our own way of saving a resource in Arches.
        inst = super().create(_no_save=True, _do_index=_do_index, **kwargs)
        inst._.to_resource(_no_save=_no_save, _do_index=_do_index)
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

        return adapter.get_adapter(key="static")
