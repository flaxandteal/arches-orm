import logging
from django.dispatch import Signal
from .translation import (
    PseudoNodeValue,
    PseudoNodeList,
    TranslationMixin,
)
from .view_models import WKRI as Resource

logger = logging.getLogger(__name__)


class ResourceModelWrapper(Resource, TranslationMixin):
    """Superclass of all well-known resources.

    When you use, `Person`, etc. it will be this class in disguise.
    """

    model_name: str
    graphid: str
    id: str
    _nodes_real: dict = None
    _nodegroup_objects_real: dict = None
    _values: dict = None
    _cross_record: dict = None
    _pending_relationships: list = None
    _related_prefetch: list = None
    resource: Resource

    def __getitem__(self, key):
        return self.__getattr__(key)

    def __setitem__(self, key, value):
        return self.__setattr__(key, value)

    def _make_pseudo_node(self, key, single=False, tile=None):
        return self._make_pseudo_node_cls(key, single=single, tile=tile, wkri=self)

    @classmethod
    def _make_pseudo_node_cls(cls, key, single=False, tile=None, wkri=None):
        nodes = cls._build_nodes()
        node_obj = cls._node_objects()[nodes[key]["nodeid"]]
        edges = cls._edges().get(nodes[key]["nodeid"])
        value = None
        if nodes[key]["datatype"][2] and not single:
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

    def __setattr__(self, key, value):
        """Set Python values for nodes attributes."""

        if key in (
            "id",
            "_root",
            "_new_id",
            "_values",
            "resource",
            "_root_node",
            "_cross_record",
            "_related_prefetch",
            "_pending_relationships",
        ):
            super().__setattr__(key, value)
        else:
            setattr(self._root().value, key, value)

    def __getattr__(self, key):
        """Retrieve Python values for nodes attributes."""

        return getattr(self._root().value, key)

    def delete(self):
        """Delete the underlying resource."""
        return self.resource.delete()

    def __init__(
        self,
        id=None,
        _new_id=None,
        resource=None,
        cross_record=None,
        related_prefetch=None,
        **kwargs,
    ):
        """Build well-known resource.

        Not normally called manually, this is the underlying constructor for
        well-known resources.
        """

        self._values = {}
        self.id = id
        self._new_id = _new_id
        self.resource = resource
        self._cross_record = cross_record
        self._related_prefetch = related_prefetch

        for key, value in kwargs.items():
            setattr(self, key, value)

    def _root(self):
        if self._root_node:
            if self._root_node.alias in self._values:
                value = self._values[self._root_node.alias]
            else:
                value = self._make_pseudo_node(
                    self._root_node.alias,
                )
                self._values[self._root_node.alias] = value
            return value

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

    def update(self, values: dict):
        """Apply a dictionary of updates to fields."""
        for key, val in values.items():
            setattr(self, key, val)

    def save(self):
        """Rebuild and save the underlying resource."""
        resource = self.to_resource(strict=True)
        resource.save()
        self.id = str(resource.pk)
        return self

    def describe(self):
        """Give a textual description of this well-known resource."""
        from tabulate import tabulate

        description = (
            f"{self.__class__.__name__}: {str(self)} <ri:{self.id} g:{self.graphid}>\n"
        )
        table = [["PROPERTY", "TYPE", "VALUE"]]
        for key, value in self._values.items():
            if value.value:
                table.append([key, value.value.__class__.__name__, str(value)])
            else:
                table.append([key, "", "(empty)"])
        return description + tabulate(table)

    def __str__(self):
        """Convert to string."""
        return str(self._wkrm.to_string(self))

    def __init_subclass__(cls, well_known_resource_model=None):
        """Create a new well-known resource model wrapper, from an WKRM."""
        if not well_known_resource_model:
            raise RuntimeError("Must try to wrap a real model")

        cls._model_name = well_known_resource_model.model_name
        cls.graphid = well_known_resource_model.graphid
        cls._wkrm = well_known_resource_model
        cls._nodes_real = {}
        cls._nodegroup_objects_real = {}
        cls.post_save = Signal()
        cls._build_nodes()
