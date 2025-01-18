from __future__ import annotations

import logging
from typing import Any
import uuid
from abc import abstractmethod, ABC
from collections.abc import Callable
from collections import UserList
from arches_orm.adapter import Adapter
from .view_models import ResourceInstanceViewModel
from .view_models.node_list import RemappedNodeListViewModel
from .errors import WKRMPermissionDenied
from .wkrm import WKRM


logger = logging.getLogger(__name__)


class ResourceWrapper(ABC):
    """Superclass of all well-known resources.

    When you use, `Person`, etc. it will be this class in disguise.
    """

    model_name: str
    view_model: type
    view_model_inst: ResourceInstanceViewModel
    graphid: str
    id: str
    _wkrm: WKRM
    _adapter: Adapter
    _values: dict | None = None
    _cross_record: dict | None = None
    _pending_relationships: list | None = None
    _related_prefetch: Callable | None = None
    _remap: bool = True
    _remap_total: bool = False
    _model_remapping: dict
    _name: str | None = None
    _description: str | None = None
    resource: Any
    proxy: bool = False

    def _can_read_resource(self):
        raise NotImplementedError()

    def _can_edit_resource(self):
        raise NotImplementedError()

    def _can_delete_resource(self):
        raise NotImplementedError()

    def _can_read_graph(self):
        raise NotImplementedError()

    def set_orm_attribute(self, key, value):
        """Set Python values for nodes attributes."""

        if key in (
            "id",
            "_new_id",
            "_values",
            "_values_real",
            "_values_list",
            "resource",
            "_root_node",
            "_context",
            "_name",
            "_description",
            "_cross_record",
            "_related_prefetch",
            "_pending_relationships",
            "_model_remapping", # NOTE: Note that this is not safe against rewriting
            "__class__",
        ):
            super().__setattr__(key, value)
        else:
            if self._remap and self._model_remapping is not None:
                if key in self._model_remapping:
                    real_key = self._model_remapping[key].replace("*", ".")
                    if "." in real_key:
                        to_get, to_set = real_key.split(".", -1)
                        got = self._get_remap(to_get)
                    else:
                        got = self.get_root()
                    if isinstance(got, UserList):
                        if len(got) == 0:
                            got = got.append()
                        elif len(got) == 1:
                            got = got[0]
                        else:
                            raise RuntimeError("Cannot set single value when multiplicity present")
                    setattr(got, to_set, value)
                elif self._remap_total:
                    raise AttributeError("Field not available in remapped model")
                else:
                    setattr(self.get_root().value, key, value)
            elif (root := self.get_root()):
                setattr(root.value, key, value)
            else:
                raise RuntimeError(f"Tried to set {key} on {self}, which has no root")

    def _get_remap(self, real_key: str):
        if real_key is None:
            raise AttributeError("Attribute not available")
        elif real_key:
            cmpt = self.get_root().value
            many = real_key.find("*")
            if many > 0:
                if "*" in real_key[many + 1:]:
                    raise RuntimeError("Can only remap a single key to one iterable")
                to_many, to_one = real_key.split("*")
                for ckey in to_many.split("."):
                    if isinstance(cmpt, UserList):
                        if len(cmpt) > 1:
                            raise RuntimeError("Can only pull out a remapped key if it has at most one >1 iterable in node hierarchy")
                        elif len(cmpt) == 1:
                            cmpt = cmpt[0]
                        else:
                            cmpt = cmpt.append()
                    cmpt = getattr(cmpt, ckey)
                if not isinstance(cmpt, UserList):
                    raise RuntimeError("Cannot have additions to a remapped multiple node unless the node has multiplicity")
                return RemappedNodeListViewModel(cmpt.nodelist, to_one)
            for ckey in real_key.split("."):
                if isinstance(cmpt, UserList):
                    if len(cmpt) > 1:
                        raise RuntimeError("Can only pull out a remapped key without a * if it has no >1 iterable in node hierarchy")
                    elif len(cmpt) == 1:
                        cmpt = cmpt[0]
                    else:
                        cmpt = cmpt.append()
                cmpt = getattr(cmpt, ckey)
            return cmpt

    def get_orm_dir(self):
        """Retrieve Python keys for nodes attributes."""

        attributes = []
        if self._remap and self._model_remapping is not None:
            if self._remap_total:
                return sorted(self._model_remapping)
            else:
                attributes += list(self._model_remapping)
        if (root := self.get_root()):
            attributes += dir(root.value)
        return attributes

    def get_orm_attribute(self, key):
        """Retrieve Python values for nodes attributes."""

        if self._remap and self._model_remapping is not None:
            if key in self._model_remapping:
                real_key = self._model_remapping[key]
                return self._get_remap(real_key)
            elif self._remap_total:
                raise AttributeError("Field not available in remapped model")
        if (root := self.get_root()):
            val = getattr(root.value, key)
        else:
            raise RuntimeError(f"Tried to get {key} on {self}, which has no root")
        return val

    def __init__(
        self,
        view_model,
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
        self.view_model_inst = view_model
        if not self._can_read_graph():
            raise WKRMPermissionDenied()
        self.id = id if isinstance(id, uuid.UUID) else uuid.UUID(id) if id else None
        self._new_id = (
            _new_id
            if isinstance(_new_id, uuid.UUID)
            else uuid.UUID(_new_id)
            if _new_id
            else None
        )
        self.resource = resource
        self._cross_record = cross_record
        self._related_prefetch = related_prefetch
        view_model._ = self

        for key, value in kwargs.items():
            self.set_orm_attribute(key, value)

    @property
    def resourceinstanceid(self):
        return self.id

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
        if not _no_save:
            inst.save()
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

        inst = cls.view_model(**values)

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

    def index(self):
        """Index the underlying resource."""
        raise NotImplementedError()

    def save(self):
        """Rebuild and save the underlying resource."""
        raise NotImplementedError()

    def describe(self):
        """Give a textual description of this well-known resource."""
        from tabulate import tabulate

        description = (
            f"{self.__class__.__name__}: {str(self)} <ri:{self.id} g:{self.graphid}>\n"
        )
        table = [["PROPERTY", "TYPE", "VALUE"]]
        for key, value in self._values.items():
            for entry in value:
                if entry.value:
                    table.append(
                        [key, entry.value.__class__.__name__, str(entry.value)]
                    )
                else:
                    table.append([key, "", "(empty)"])
        return description + tabulate(table)

    def to_string(self):
        """Convert to string."""
        return str(self._wkrm.to_string(self))

    def __init_subclass__(cls, well_known_resource_model=None, proxy=None, context=None):
        """Create a new well-known resource model wrapper, from an WKRM."""
        if proxy is not None:
            cls.proxy = proxy
        if not cls.proxy:
            if not well_known_resource_model:
                raise RuntimeError("Must try to wrap a real model")

            if context is None:
                raise RuntimeError("Must have an adapter to create classes")

            cls._context = context
            cls._model_name = well_known_resource_model.model_name
            cls._model_class_name = well_known_resource_model.model_class_name
            cls._model_remapping = well_known_resource_model.remapping
            cls._remap_total = well_known_resource_model.total_remap
            cls.graphid = well_known_resource_model.graphid
            cls._wkrm = well_known_resource_model
            cls._add_events()

    @classmethod
    @abstractmethod
    def _add_events(cls):
        """Add events to this model."""

    @classmethod
    @abstractmethod
    def search(cls, text, fields=None, _total=None):
        """Search for resources of this model, and return as well-known resources."""

    @classmethod
    @abstractmethod
    def all_ids(cls):
        """Get IDs for all resources of this type."""

    @classmethod
    @abstractmethod
    def all(cls, related_prefetch: Callable[[str], "ResourceWrapper"] | None=None, limit: int | None=None) -> list["ResourceWrapper"]:
        """Get all resources of this type."""

    @classmethod
    @abstractmethod
    def find(cls, resourceinstanceid):
        """Find an individual well-known resource by instance ID."""

    @abstractmethod
    def delete(self):
        """Delete the underlying resource."""

    @abstractmethod
    def remove(self):
        """When called via a relationship (dot), remove the relationship."""

    @abstractmethod
    def append(self, _no_save=False):
        """When called via a relationship (dot), append to the relationship."""

    @classmethod
    @abstractmethod
    def where(cls, cross_record=None, **kwargs):
        """Do a filtered query returning a list of well-known resources."""

    @staticmethod
    @abstractmethod
    def get_adapter():
        """Get the adapter that encapsulates this wrapper."""

    @abstractmethod
    def reload(self, ignore_prefetch=True):
        """Reload field values, but not node values for class."""

    @abstractmethod
    def get_root(self):
        """Get the root value."""
