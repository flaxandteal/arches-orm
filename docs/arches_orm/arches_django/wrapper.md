# Module arches_orm.arches_django.wrapper

??? example "View Source"
        from arches.app.models.resource import Resource

        from django.dispatch import Signal

        from functools import lru_cache

        from datetime import datetime

        from arches.app.models.models import ResourceXResource, Node, NodeGroup, Edge

        from arches.app.models.tile import Tile as TileProxyModel

        from arches.app.models.system_settings import settings as system_settings

        from collections import UserList

        import logging

        from arches_orm.view_models import ViewModel, NodeListViewModel

        from arches_orm.wrapper import AdapterManager, ResourceWrapper

        from .datatypes import get_view_model_for_datatype

        logger = logging.getLogger(__name__)

        

        LOAD_FULL_NODE_OBJECTS = True

        LOAD_ALL_NODES = True

        class ArchesDjangoAdapter:

            def __str__(self):

                return "arches-django"

            def get_wrapper(self):

                return ArchesDjangoResourceWrapper

            def load_from_id(self, resource_id, from_prefetch=None):

                from arches_orm.utils import get_resource_models_for_adapter

                resource = (

                    from_prefetch(resource_id)

                    if from_prefetch is not None

                    else Resource.objects.get(pk=resource_id)

                )

                resource_models_by_graph_id = get_resource_models_for_adapter(str(self))["by-graph-id"]

                if str(resource.graph_id) not in resource_models_by_graph_id:

                    logger.error("Tried to load non-existent WKRM: %s", resource_id)

                    return None

                return resource_models_by_graph_id[str(resource.graph_id)].from_resource(

                    resource, related_prefetch=from_prefetch

                )

            def get_hooks(self):

                from .hooks import HOOKS

                return HOOKS

        

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

        

        class ArchesDjangoResourceWrapper(ResourceWrapper, adapter=True):

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

                        elif root_node and node["nodeid"] == str(root_node.nodeid):

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

                cls, node_objs, resource, related_prefetch=None, wkri=None

            ):

                """Populate fields from the ID-referenced Arches resource."""

                all_values = {}

                # load_tiles thins by user

                resource.tiles = TileProxyModel.objects.filter(resourceinstance=resource)

                for tile in resource.tiles:

                    if tile.data:

                        for nodeid, node_value in tile.data.items():

                            if nodeid in node_objs:

                                key = node_objs[nodeid]

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

            def _make_pseudo_node(self, key, single=False, tile=None):

                return self._make_pseudo_node_cls(key, single=single, tile=tile, wkri=self)

            @classmethod

            def _make_pseudo_node_cls(cls, key, single=False, tile=None, wkri=None):

                nodes = cls._build_nodes()

                node_obj = cls._node_objects()[nodes[key].nodeid]

                nodegroups = cls._nodegroup_objects()

                edges = cls._edges().get(nodes[key].nodeid)

                value = None

                if node_obj.nodegroup_id and nodegroups[str(node_obj.nodegroup_id)].cardinality == "n":

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

            def __init_subclass__(cls, well_known_resource_model=None):

                super().__init_subclass__(well_known_resource_model=well_known_resource_model)

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

## Variables

```python3
LOAD_ALL_NODES
```

```python3
LOAD_FULL_NODE_OBJECTS
```

```python3
logger
```

## Classes

### ArchesDjangoAdapter

```python3
class ArchesDjangoAdapter(
    /,
    *args,
    **kwargs
)
```

??? example "View Source"
        class ArchesDjangoAdapter:

            def __str__(self):

                return "arches-django"

            def get_wrapper(self):

                return ArchesDjangoResourceWrapper

            def load_from_id(self, resource_id, from_prefetch=None):

                from arches_orm.utils import get_resource_models_for_adapter

                resource = (

                    from_prefetch(resource_id)

                    if from_prefetch is not None

                    else Resource.objects.get(pk=resource_id)

                )

                resource_models_by_graph_id = get_resource_models_for_adapter(str(self))["by-graph-id"]

                if str(resource.graph_id) not in resource_models_by_graph_id:

                    logger.error("Tried to load non-existent WKRM: %s", resource_id)

                    return None

                return resource_models_by_graph_id[str(resource.graph_id)].from_resource(

                    resource, related_prefetch=from_prefetch

                )

            def get_hooks(self):

                from .hooks import HOOKS

                return HOOKS

------

#### Methods

    
#### get_hooks

```python3
def get_hooks(
    self
)
```

??? example "View Source"
            def get_hooks(self):

                from .hooks import HOOKS

                return HOOKS

    
#### get_wrapper

```python3
def get_wrapper(
    self
)
```

??? example "View Source"
            def get_wrapper(self):

                return ArchesDjangoResourceWrapper

    
#### load_from_id

```python3
def load_from_id(
    self,
    resource_id,
    from_prefetch=None
)
```

??? example "View Source"
            def load_from_id(self, resource_id, from_prefetch=None):

                from arches_orm.utils import get_resource_models_for_adapter

                resource = (

                    from_prefetch(resource_id)

                    if from_prefetch is not None

                    else Resource.objects.get(pk=resource_id)

                )

                resource_models_by_graph_id = get_resource_models_for_adapter(str(self))["by-graph-id"]

                if str(resource.graph_id) not in resource_models_by_graph_id:

                    logger.error("Tried to load non-existent WKRM: %s", resource_id)

                    return None

                return resource_models_by_graph_id[str(resource.graph_id)].from_resource(

                    resource, related_prefetch=from_prefetch

                )

### ArchesDjangoResourceWrapper

```python3
class ArchesDjangoResourceWrapper(
    id=None,
    _new_id=None,
    resource=None,
    cross_record=None,
    related_prefetch=None,
    **kwargs
)
```

Superclass of all well-known resources.

When you use, `Person`, etc. it will be this class in disguise.

??? example "View Source"
        class ArchesDjangoResourceWrapper(ResourceWrapper, adapter=True):

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

                        elif root_node and node["nodeid"] == str(root_node.nodeid):

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

                cls, node_objs, resource, related_prefetch=None, wkri=None

            ):

                """Populate fields from the ID-referenced Arches resource."""

                all_values = {}

                # load_tiles thins by user

                resource.tiles = TileProxyModel.objects.filter(resourceinstance=resource)

                for tile in resource.tiles:

                    if tile.data:

                        for nodeid, node_value in tile.data.items():

                            if nodeid in node_objs:

                                key = node_objs[nodeid]

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

            def _make_pseudo_node(self, key, single=False, tile=None):

                return self._make_pseudo_node_cls(key, single=single, tile=tile, wkri=self)

            @classmethod

            def _make_pseudo_node_cls(cls, key, single=False, tile=None, wkri=None):

                nodes = cls._build_nodes()

                node_obj = cls._node_objects()[nodes[key].nodeid]

                nodegroups = cls._nodegroup_objects()

                edges = cls._edges().get(nodes[key].nodeid)

                value = None

                if node_obj.nodegroup_id and nodegroups[str(node_obj.nodegroup_id)].cardinality == "n":

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

            def __init_subclass__(cls, well_known_resource_model=None):

                super().__init_subclass__(well_known_resource_model=well_known_resource_model)

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

------

#### Ancestors (in MRO)

* arches_orm.wrapper.ResourceWrapper
* arches_orm.view_models.WKRI

#### Descendants

* arches_orm.wkrm.Person

#### Static methods

    
#### all

```python3
def all(
    related_prefetch=None
)
```

Get all resources of this type.

??? example "View Source"
            @classmethod

            def all(cls, related_prefetch=None):

                """Get all resources of this type."""

                resources = Resource.objects.filter(graph_id=cls.graphid).all()

                return [

                    cls.from_resource(resource, related_prefetch=related_prefetch)

                    for resource in resources

                ]

    
#### all_ids

```python3
def all_ids(
    
)
```

Get IDs for all resources of this type.

??? example "View Source"
            @classmethod

            def all_ids(cls):

                """Get IDs for all resources of this type."""

                return list(

                    Resource.objects.filter(graph_id=cls.graphid).values_list(

                        "resourceinstanceid", flat=True

                    )

                )

    
#### build

```python3
def build(
    **kwargs
)
```

Create a new well-known resource.

Makes a well-known resource but not (yet) Arches resource,
from field values.

??? example "View Source"
            @classmethod

            def build(cls, **kwargs):

                """Create a new well-known resource.

                Makes a well-known resource but not (yet) Arches resource,

                from field values.

                """

                values = {}

                for key, arg in kwargs.items():

                    if "." not in key:

                        values[key] = arg

                inst = cls(**values)

                for key, val in kwargs.items():

                    if "." in key:

                        level = inst

                        for token in key.split(".")[:-1]:

                            level = getattr(level, token)

                        setattr(level, key.split(".")[-1], val)

                return inst

    
#### create

```python3
def create(
    _no_save=False,
    _do_index=True,
    **kwargs
)
```

Create a new well-known resource and Arches resource from field values.

??? example "View Source"
            @classmethod

            def create(cls, _no_save=False, _do_index=True, **kwargs):

                # We have our own way of saving a resource in Arches.

                inst = super().create(_no_save=True, _do_index=_do_index, **kwargs)

                inst.to_resource(_no_save=_no_save, _do_index=_do_index)

                return inst

    
#### create_bulk

```python3
def create_bulk(
    fields: list,
    do_index: bool = True
)
```

??? example "View Source"
            @classmethod

            def create_bulk(cls, fields: list, do_index: bool = True):

                raise NotImplementedError("The bulk_create module needs to be rewritten")

    
#### find

```python3
def find(
    resourceinstanceid,
    from_prefetch=None
)
```

Find an individual well-known resource by instance ID.

??? example "View Source"
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

    
#### from_resource

```python3
def from_resource(
    resource,
    cross_record=None,
    related_prefetch=None
)
```

Build a well-known resource from an Arches resource.

??? example "View Source"
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

    
#### from_resource_instance

```python3
def from_resource_instance(
    resourceinstance,
    cross_record=None
)
```

Build a well-known resource from a resource instance.

??? example "View Source"
            @classmethod

            def from_resource_instance(cls, resourceinstance, cross_record=None):

                """Build a well-known resource from a resource instance."""

                resource = Resource(resourceinstance.resourceinstanceid)

                return cls.from_resource(resource, cross_record=cross_record)

    
#### get_adapter

```python3
def get_adapter(
    
)
```

Get the adapter that encapsulates this wrapper.

??? example "View Source"
            @staticmethod

            def get_adapter():

                return ArchesDjangoAdapter()

    
#### search

```python3
def search(
    text,
    fields=None,
    _total=None
)
```

Search ES for resources of this model, and return as well-known resources.

??? example "View Source"
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

    
#### values_from_resource

```python3
def values_from_resource(
    node_objs,
    resource,
    related_prefetch=None,
    wkri=None
)
```

Populate fields from the ID-referenced Arches resource.

??? example "View Source"
            @classmethod

            def values_from_resource(

                cls, node_objs, resource, related_prefetch=None, wkri=None

            ):

                """Populate fields from the ID-referenced Arches resource."""

                all_values = {}

                # load_tiles thins by user

                resource.tiles = TileProxyModel.objects.filter(resourceinstance=resource)

                for tile in resource.tiles:

                    if tile.data:

                        for nodeid, node_value in tile.data.items():

                            if nodeid in node_objs:

                                key = node_objs[nodeid]

                                if node_value is not None:

                                    all_values[key] = cls._make_pseudo_node_cls(

                                        key, tile=tile, wkri=wkri

                                    )

                return all_values

    
#### where

```python3
def where(
    cross_record=None,
    **kwargs
)
```

Do a filtered query returning a list of well-known resources.

??? example "View Source"
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

#### Methods

    
#### append

```python3
def append(
    self,
    _no_save=False
)
```

When called via a relationship (dot), append to the relationship.

??? example "View Source"
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

    
#### delete

```python3
def delete(
    self
)
```

Delete the underlying resource.

??? example "View Source"
            def delete(self):

                """Delete the underlying resource."""

                return self.resource.delete()

    
#### describe

```python3
def describe(
    self
)
```

Give a textual description of this well-known resource.

??? example "View Source"
            def describe(self):

                """Give a textual description of this well-known resource."""

                from tabulate import tabulate

                description = (

                    f"{self.__class__.__name__}: {str(self)} <ri:{self.id} g:{self.graphid}>\n"

                )

                table = [["PROPERTY", "TYPE", "VALUE"]]

                for key, value in self._values.items():

                    if isinstance(value, list):

                        if value:

                            table.append([key, value[0].__class__.__name__, str(value[0])])

                            for val in value[1:]:

                                table.append(["", val.__class__.__name__, str(val)])

                        else:

                            table.append([key, "", "(empty)"])

                    else:

                        table.append([key, value.value.__class__.__name__, str(value)])

                return description + tabulate(table)

    
#### get_root

```python3
def get_root(
    self
)
```

??? example "View Source"
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

    
#### remove

```python3
def remove(
    self
)
```

When called via a relationship (dot), remove the relationship.

??? example "View Source"
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

    
#### save

```python3
def save(
    self
)
```

Rebuild and save the underlying resource.

??? example "View Source"
            def save(self):

                """Rebuild and save the underlying resource."""

                resource = self.to_resource(strict=True)

                resource.save()

                self.id = resource.pk

                return self

    
#### to_resource

```python3
def to_resource(
    self,
    verbose=False,
    strict=False,
    _no_save=False,
    _known_new=False,
    _do_index=True
)
```

Construct an Arches resource.

This may be new or existing, for this well-known resource.

??? example "View Source"
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

    
#### update

```python3
def update(
    self,
    values: dict
)
```

Apply a dictionary of updates to fields.

??? example "View Source"
            def update(self, values: dict):

                """Apply a dictionary of updates to fields."""

                for key, val in values.items():

                    setattr(self, key, val)

### PseudoNodeList

```python3
class PseudoNodeList(
    node,
    parent
)
```

A more or less complete user-defined wrapper around list objects.

??? example "View Source"
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

------

#### Ancestors (in MRO)

* collections.UserList
* collections.abc.MutableSequence
* collections.abc.Sequence
* collections.abc.Reversible
* collections.abc.Collection
* collections.abc.Sized
* collections.abc.Iterable
* collections.abc.Container

#### Methods

    
#### append

```python3
def append(
    self,
    item=None
)
```

S.append(value) -- append value to the end of the sequence

??? example "View Source"
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

    
#### clear

```python3
def clear(
    self
)
```

S.clear() -> None -- remove all items from S

??? example "View Source"
            def clear(self):

                self.data.clear()

    
#### copy

```python3
def copy(
    self
)
```

??? example "View Source"
            def copy(self):

                return self.__class__(self)

    
#### count

```python3
def count(
    self,
    item
)
```

S.count(value) -> integer -- return number of occurrences of value

??? example "View Source"
            def count(self, item):

                return self.data.count(item)

    
#### extend

```python3
def extend(
    self,
    other
)
```

S.extend(iterable) -- extend sequence by appending elements from the iterable

??? example "View Source"
            def extend(self, other):

                if isinstance(other, UserList):

                    self.data.extend(other.data)

                else:

                    self.data.extend(other)

    
#### get_children

```python3
def get_children(
    self,
    direct=None
)
```

??? example "View Source"
            def get_children(self, direct=None):

                return self

    
#### get_relationships

```python3
def get_relationships(
    self
)
```

??? example "View Source"
            def get_relationships(self):

                return []

    
#### get_tile

```python3
def get_tile(
    self
)
```

??? example "View Source"
            def get_tile(self):

                for pseudo_node in self:

                    pseudo_node.get_tile()

                return None

    
#### index

```python3
def index(
    self,
    item,
    *args
)
```

S.index(value, [start, [stop]]) -> integer -- return first index of value.

Raises ValueError if the value is not present.

Supporting start and stop arguments is optional, but
recommended.

??? example "View Source"
            def index(self, item, *args):

                return self.data.index(item, *args)

    
#### insert

```python3
def insert(
    self,
    i,
    item
)
```

S.insert(index, value) -- insert value before index

??? example "View Source"
            def insert(self, i, item):

                self.data.insert(i, item)

    
#### pop

```python3
def pop(
    self,
    i=-1
)
```

S.pop([index]) -> item -- remove and return item at index (default last).

Raise IndexError if list is empty or index is out of range.

??? example "View Source"
            def pop(self, i=-1):

                return self.data.pop(i)

    
#### remove

```python3
def remove(
    self,
    item
)
```

S.remove(value) -- remove first occurrence of value.

Raise ValueError if the value is not present.

??? example "View Source"
            def remove(self, item):

                self.data.remove(item)

    
#### reverse

```python3
def reverse(
    self
)
```

S.reverse() -- reverse *IN PLACE*

??? example "View Source"
            def reverse(self):

                self.data.reverse()

    
#### sort

```python3
def sort(
    self,
    /,
    *args,
    **kwds
)
```

??? example "View Source"
            def sort(self, /, *args, **kwds):

                self.data.sort(*args, **kwds)

    
#### value_list

```python3
def value_list(
    self
)
```

??? example "View Source"
            def value_list(self):

                return NodeListViewModel(self)

### PseudoNodeValue

```python3
class PseudoNodeValue(
    node,
    tile=None,
    value=None,
    parent=None,
    child_nodes=None
)
```

??? example "View Source"
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

------

#### Instance variables

```python3
value
```

#### Methods

    
#### get_children

```python3
def get_children(
    self,
    direct=None
)
```

??? example "View Source"
            def get_children(self, direct=None):

                if self.value:

                    try:

                        return self.value.get_children(direct=direct)

                    except AttributeError:

                        ...

                return []

    
#### get_relationships

```python3
def get_relationships(
    self
)
```

??? example "View Source"
            def get_relationships(self):

                try:

                    return self.value.get_relationships() if self.value else []

                except AttributeError:

                    return []

    
#### get_tile

```python3
def get_tile(
    self
)
```

??? example "View Source"
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