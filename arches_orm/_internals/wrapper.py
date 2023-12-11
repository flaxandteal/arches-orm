from arches.app.models.resource import Resource
from functools import lru_cache
import logging
from django.dispatch import Signal
from arches.app.models.models import ResourceXResource, Node, NodeGroup
from arches.app.models.tile import Tile as TileProxyModel
from arches.app.models.system_settings import settings as system_settings
from .translation import TranslationMixin, LOAD_ALL_NODES, LOAD_FULL_NODE_OBJECTS
from .relations import RelationList

logger = logging.getLogger(__name__)


class ResourceModelWrapper(TranslationMixin):
    """Superclass of all well-known resources.

    When you use, `Person`, etc. it will be this class in disguise.
    """

    model_name: str
    graphid: str
    id: str
    _nodes: dict = None
    _nodes_real: dict = None
    _values: dict = None
    _cross_record: dict = None
    _lazy: bool = False
    _filled: bool = False
    _related_prefetch = None
    __datatype_factory = None
    __node_datatypes = None
    resource: Resource

    def __getitem__(self, key):
        return self.__getattr__(key)

    def __setitem__(self, key, value):
        return self.__setattr__(key, value)

    def __setattr__(self, key, value):
        """Standard dot-notation ORM implementation.

        Allows for lazy evaluation, so if tiles have not been pulled,
        reaching in will cause them to be loaded.
        """

        key, value = self._set_value(key, value)
        if key in ("_values", "_lazy", "_filled", "resource", "_cross_record"):
            super().__setattr__(key, value)
        else:
            if self._lazy and not self._filled:
                self.fill_from_resource(self._related_prefetch)
            self._values[key] = value

    def __getattr__(self, key):
        """Retrieve Python values for nodes attributes."""

        if key in self._values:
            return self._values[key]
        elif key in self._nodes:
            if self._lazy and not self._filled:
                self.fill_from_resource(self._related_prefetch)
                return self.__getattr__(key)
            # Semantic nodes say they don't collect multiple values, but they have multiple children
            return (
                []
                if (datatype := self._nodes[key].get("datatype", None))
                and datatype[1].collects_multiple_values()
                or datatype[0] == "semantic"
                else None
            )
        raise AttributeError(f"No well-known attribute {key}")

    def delete(self):
        """Delete the underlying resource."""
        return self.resource.delete()

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

    def __init__(
        self,
        id=None,
        _new_id=None,
        resource=None,
        x=None,
        filled=True,
        related_prefetch=None,
        lazy=False,
        **kwargs,
    ):
        """Not normally called manually, this is the underlying constructor for well-known resources."""

        self._values = {}
        self.id = id
        self._new_id = _new_id
        self.resource = resource
        self._cross_record = x
        self._filled = filled
        self._lazy = lazy
        self._related_prefetch = related_prefetch

        if set(kwargs) - set(self._nodes):
            raise NotImplementedError(
                f"Some keys in {', '.join(kwargs)} are not well-known in {type(self)}"
            )
        if not filled and not lazy:
            self.fill_from_resource(
                reload=True, related_prefetch=self._related_prefetch
            )

        for key, value in kwargs.items():
            if isinstance(value, list) and any(
                types := [isinstance(entry, ResourceModelWrapper) for entry in value]
            ):
                if not all(types):
                    raise NotImplementedError(
                        "Cannot currently handle mixed ResourceModelWrapper/non-ResourceModelWrapper lists"
                    )
                typ = self._nodes[key]["type"]
                kwargs[key] = RelationList(self, key, self._nodes[key]["nodeid"], None)
                for resource in value:
                    kwargs[key].append(resource)

        self._values.update(kwargs)

    def _set_value(self, key, arg):
        """Real implementation of data-setting for __setattr__, allowing dot-setting."""

        if "." in key:
            node, prop = key.split(".")
            typ = self._nodes[node]["type"]
            if not typ.startswith("@"):
                raise RuntimeError(
                    "Relationship must be with a resource model, not e.g. a primitive type"
                )
            typ = typ[1:]
            datum = {}
            datum["wkriFrom"] = self
            datum["wkriFromKey"] = node
            datum["wkriFromNodeid"] = self._nodes[node]["nodeid"]
            resource_cls = get_well_known_resource_model_by_class_name(typ)
            if not isinstance(arg, list):
                arg = [arg]

            all_resources = []
            for val in arg:
                resources = resource_cls.where(x=datum, **{prop: val})
                if not resources:
                    raise KeyError(f"Related resource for {key} not found: {val}")
                if len(resources) > 1:
                    raise KeyError(f"Multiple related resources for {key} found: {val}")
                all_resources += resources
            return node, all_resources
        else:
            return key, arg

    @classmethod
    def create_bulk(cls, fields: list, do_index: bool = True):
        raise NotImplementedError("The bulk_create module needs to be rewritten")

    @classmethod
    def create(cls, _no_save=False, _do_index=True, **kwargs):
        """Create a new well-known resource and Arches resource from field values."""

        # If an ID is supplied, it should be treated as desired, not existing.
        if "id" in kwargs:
            kwargs["_new_id"] = kwargs["id"]
            del kwargs["id"]
        inst = cls.build(**kwargs)
        inst.to_resource(_no_save=_no_save, _do_index=_do_index)
        return inst

    @classmethod
    def build(cls, **kwargs):
        """Create a new well-known resource, but not (yet) Arches resource, from field values."""

        values = {}
        for key, arg in kwargs.items():
            if "." not in key:
                values[key] = arg

        inst = cls(**values)

        for key, val in kwargs.items():
            if "." in key:
                setattr(inst, key, val)

        return inst

    def update(self, values: dict):
        """Apply a dictionary of updates to fields."""
        for key, val in values.items():
            setattr(self, key, val)

    def save(self):
        """Rebuild and save the underlying resource."""
        resource = self.to_resource(strict=True)

    @classmethod
    def search(cls, text, fields=None, _total=None, _include_provisional=True):
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
        total = _total or 0
        include_provisional = _include_provisional
        se = SearchEngineFactory().create()
        # TODO: permitted_nodegroups = get_permitted_nodegroups(request.user)
        permitted_nodegroups = [
            node["nodegroupid"]
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
    def find(cls, resourceinstanceid):
        """Find an individual well-known resource by instance ID."""
        resource = Resource.objects.get(resourceinstanceid=resourceinstanceid)
        if str(resource.graph_id) != cls.graphid:
            raise RuntimeError(
                f"Using find against wrong resource type: {resource.graph_id} for {cls.graphid}"
            )
        if resource:
            return cls.from_resource(resource)
        return None

    def describe(self):
        """Give a textual description of this well-known resource."""
        from tabulate import tabulate

        description = (
            f"{self.__class__.__name__}: {str(self)} <ri:{self.id} g:{self.graphid}>\n"
        )
        table = [["PROPERTY", "TYPE", "VALUE"]]
        for key, value in self._values.items():
            if isinstance(value, list) or isinstance(value, RelationList):
                if value:
                    table.append([key, value[0].__class__.__name__, str(value[0])])
                    for val in value[1:]:
                        table.append(["", val.__class__.__name__, str(val)])
                else:
                    table.append([key, "", "(empty)"])
            else:
                table.append([key, value.__class__.__name__, str(value)])
        return description + tabulate(table)

    @classmethod
    def where(cls, x=None, **kwargs):
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
            nodegroup_id=cls._nodes[key]["nodegroupid"],
            data__contains={cls._nodes[key]["nodeid"]: value},
        )
        return [
            cls.from_resource_instance(tile.resourceinstance, x=x) for tile in tiles
        ]

    def __str__(self):
        """Convert to string."""
        return str(self._wkrm.to_string(self))

    @property
    def _nodes(self):
        self._build_nodes()
        return self._nodes_real

    @classmethod
    @lru_cache
    def _build_nodes(cls):
        nodes: dict[str, dict] = {}
        if LOAD_FULL_NODE_OBJECTS and LOAD_ALL_NODES:
            for node_obj in cls._node_objects(load_all=True).values():
                # The root node will not have a nodegroup, but we do not need it
                if node_obj.nodegroup_id:
                    nodes[str(node_obj.alias)] = {
                        "nodeid": str(node_obj.nodeid),
                        "nodegroupid": str(node_obj.nodegroup_id),
                        "type": node_obj.datatype,
                    }
            # Ensure defined nodes overwrite the autoloaded ones
            nodes.update(cls._wkrm.nodes)
            nodegroups = cls._nodegroup_objects()
            for node in nodes.values():
                if (nodegroup := nodegroups.get(
                    node["nodegroupid"]
                )):
                    if nodegroup.parentnodegroup_id:
                        node["parentnodegroup_id"] = str(nodegroup.parentnodegroup_id)
                else:
                    raise KeyError("Missing nodegroups based on WKRM")
        for node in nodes.values():
            node["datatype"] = cls._datatype(node["nodeid"])
        cls._nodes_real = nodes

    def __init_subclass__(cls, well_known_resource_model=None):
        """Create a new well-known resource model wrapper, from an WKRM."""
        if not well_known_resource_model:
            raise RuntimeError("Must try to wrap a real model")

        cls._model_name = well_known_resource_model.model_name
        cls.graphid = well_known_resource_model.graphid
        cls._wkrm = well_known_resource_model
        cls._nodes_real = {}
        cls.post_save = Signal()

    @classmethod
    @lru_cache
    def _datatype(cls, nodeid):
        """Caching datatype retrieval (possibly unnecessary)."""
        datatype = cls._node_datatypes()[nodeid]
        datatype_instance = cls._datatype_factory().get_instance(datatype)
        return datatype, datatype_instance

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
    def _node_objects(cls, load_all=False):
        """Caching retrieval of all Arches nodes for this model."""
        if not LOAD_FULL_NODE_OBJECTS:
            raise RuntimeError("Attempt to load full node objects when asked not to")

        if load_all:
            fltr = {"graph_id": cls.graphid}
        else:
            fltr = {"nodeid__in": [node["nodeid"] for node in cls._nodes.values()]}
        return {str(node.nodeid): node for node in Node.objects.filter(**fltr)}

    @classmethod
    @lru_cache
    def _nodegroup_objects(cls) -> dict[str, NodeGroup]:
        """Caching retrieval of all Arches nodegroups for this model."""
        if not LOAD_FULL_NODE_OBJECTS:
            raise RuntimeError("Attempt to load full node objects when asked not to")

        return {
            str(nodegroup.nodegroupid): nodegroup
            for nodegroup in NodeGroup.objects.filter(
                nodegroupid__in=[node["nodegroupid"] for node in cls._nodes.values()]
            )
        }

    @classmethod
    def _node_datatypes(cls):
        """Caching retrieval of datatypes for Arches nodes in this model."""
        if cls.__node_datatypes is None:
            cls.__node_datatypes = {
                str(nodeid): datatype
                for nodeid, datatype in Node.objects.filter(
                    nodeid__in=[node["nodeid"] for node in cls._nodes.values()]
                ).values_list("nodeid", "datatype")
            }
        return cls.__node_datatypes

    @classmethod
    def from_resource_instance(cls, resourceinstance, x=None):
        """Build a well-known resource from a resource instance."""
        resource = Resource(resourceinstance.resourceinstanceid)
        return cls.from_resource(resource, x=x)

    @classmethod
    def from_resource(cls, resource, x=None, lazy=False, related_prefetch=None):
        """Build a well-known resource from an Arches resource."""
        ri = cls(
            id=resource.resourceinstanceid,
            resource=resource,
            x=x,
            filled=False,
            lazy=lazy,
            related_prefetch=related_prefetch,
        )
        return ri
