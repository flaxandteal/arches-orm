from typing import Union, Any
import uuid
from functools import cached_property, lru_cache
from django.contrib.auth.models import User
from arches.app.models.models import Node, ResourceInstance
from arches.app.datatypes.datatypes import (
    ResourceInstanceDataType,
    ResourceInstanceListDataType,
    StringDataType,
)
from arches.app.datatypes.concept_types import (
    ConceptDataType,
    BaseConceptDataType,
    ConceptListDataType,
)
from arches.app.datatypes.base import BaseDataType
from arches.app.models.tile import Tile
from arches.app.models.resource import Resource
from collections import UserDict, UserList
from collections.abc import Iterable
from .relations import WKRI


class ViewModelFactory(UserDict):
    @cached_property
    def _datatype_factory(self):
        """Caching datatype factory retrieval (possibly unnecessary)."""
        from arches.app.datatypes.datatypes import DataTypeFactory

        return DataTypeFactory()

    def make(
        self,
        tile: Tile,
        node: Node,
        value: Any = None,
        parent: Any = None,
        related_prefetch=None,
    ):
        datatype = self._datatype_factory.get_instance(node.datatype)
        if node.datatype in self:
            if node.datatype.startswith("resource-instance"):
                return self[node.datatype].from_triple(
                    tile, node, value, parent, datatype, related_prefetch
                )
            else:
                return self[node.datatype].from_triple(
                    tile, node, value, parent, datatype
                )
        else:
            return datatype.transform_value_for_tile(
                value or tile.data, **node.get("config", {})
            )

    def __call__(self, typ):
        def wrapper(fn):
            self[typ] = fn
            return fn

        return wrapper


REGISTER = ViewModelFactory()


def get_view_model_for_datatype(tile, node, parent, value=None, related_prefetch=None):
    return REGISTER.make(
        tile, node, value=value, parent=parent, related_prefetch=related_prefetch
    )


@REGISTER("user")
class UserViewModel(str):
    """Wraps a user, so that a Django User can be obtained.

    To access the actual user, use `.user`.
    """

    _tile: Tile
    _node: Node
    _user_datatype: BaseDataType

    def __eq__(self, other):
        return self.user == other.user

    @classmethod
    def from_triple(cls, tile, node, value, parent, user_datatype):
        return cls(tile, node, value, user_datatype)

    def __new__(cls, tile, node, value: User | int | None, user_datatype):
        if value:
            if isinstance(value, User):
                tile.data[str(node.nodeid)] = value.pk
            else:
                tile.data[str(node.nodeid)] = value
                display_value = value

        display_value = user_datatype.get_display_value(
            tile,
            node,
        )
        mystr = super(UserViewModel, cls).__new__(cls, display_value)
        cls._tile = tile
        cls._node = node
        cls._user_datatype = user_datatype
        return mystr

    @property
    def user(self):
        user = User.objects.get(pk=int(self._tile.data[str(self._node.nodeid)]))
        return user

    def as_tile_data(self):
        return self.user.pk


@REGISTER("string")
class StringViewModel(str):
    """Wraps a string, allowing language translation.

    Subclasses str, but also allows `.lang("zh")`, etc. to re-translate.
    """

    _tile: Tile
    _node: Node
    _string_datatype: StringDataType

    @classmethod
    def from_triple(cls, tile, node, value: dict | None, parent, datatype):
        return cls(tile, node, value, datatype)

    def __new__(
        cls, tile, node, value: dict | str | None, string_datatype, language=None
    ):
        if value is not None:
            tile.data.setdefault(str(node.nodeid), {})
            if isinstance(value, dict):
                tile.data[str(node.nodeid)].update(value)
            else:
                tile.data[str(node.nodeid)] = string_datatype.transform_value_for_tile(
                    value
                )
        display_value = string_datatype.get_display_value(tile, node, language=language)
        mystr = super(StringViewModel, cls).__new__(cls, display_value)
        mystr._tile = tile
        mystr._node = node
        mystr._string_datatype = string_datatype
        return mystr

    def lang(self, language):
        return self._string_datatype.get_display_value(
            self._tile, self._node, language=language
        )

    def as_tile_data(self):
        changed = self._string_datatype.transform_value_for_tile(str(self))

        # We do not want to lose all languages, because we only display one per string,
        # but if there is a change, then all languages should go (until we have a
        # multilingual version of the view model)
        if self._tile.data and str(self._node.nodeid) in self._tile.data:
            for key, val in changed.items():
                if self._tile.data[str(self._node.nodeid)].get(key) != val:
                    return changed
            return self._tile.data[str(self._node.nodeid)]
        return changed


@REGISTER("concept")
class ConceptValueViewModel(str):
    """Wraps a concept, allowing interrogation.

    Subclasses str, so it can be handled like a string enum, but keeps
    the `.value`, `.lang` and `.text` properties cached, so you can
    find out more.
    """

    _concept_value_id: uuid.UUID
    _concept_datatype: ConceptDataType

    @classmethod
    def from_triple(cls, tile, node, value: uuid.UUID | str | None, parent, datatype):
        if value is not None:
            tile.data = value
        return cls(tile.data, datatype)

    def __eq__(self, other):
        return self.conceptid == other.conceptid

    def __new__(
        cls,
        concept_value_id: Union[str, uuid.UUID],
        concept_datatype: BaseConceptDataType,
    ):
        _concept_value_id: uuid.UUID = (
            concept_value_id
            if isinstance(concept_value_id, uuid.UUID)
            else uuid.UUID(concept_value_id)
        )
        mystr = super(ConceptValueViewModel, cls).__new__(cls, str(_concept_value_id))
        mystr._concept_value_id = _concept_value_id
        mystr._concept_datatype = concept_datatype
        return mystr

    @property
    @lru_cache
    def conceptid(self):
        return self.value.concept_id

    @property
    @lru_cache
    def concept(self):
        return self.value.concept

    @property
    @lru_cache
    def value(self):
        return self._concept_datatype.get_value(self._concept_value_id)

    @property
    @lru_cache
    def text(self):
        return self.value.value

    @property
    @lru_cache
    def lang(self):
        return self.value.language

    def __str__(self):
        return self.text

    def __repr__(self):
        return f"{self.value.concept_id}>{self._concept_value_id}[{self.text}]"

    def as_tile_data(self):
        return str(self._concept_value_id)


@REGISTER("concept-list")
class ConceptListValueViewModel(UserList):
    """Wraps a concept list, allowing interrogation.

    Subclasses list, so its members can be handled like a string enum, but keeps
    the `.value`, `.lang` and `.text` properties cached, so you can
    find out more.
    """

    _tile: Tile
    _node: Node
    _concept_list_datatype: BaseDataType

    @classmethod
    def from_triple(
        cls, tile, node, value: list[uuid.UUID | str] | None, parent, datatype
    ):
        if value is not None:
            tile.data = value
        return cls(tile.data, datatype, tile, node)

    def __init__(
        self,
        concept_value_ids: Iterable[str | uuid.UUID],
        concept_list_datatype: ConceptListDataType,
        tile,
        node,
    ):
        self._concept_list_datatype = concept_list_datatype
        for concept_value_id in concept_value_ids:
            self.append(concept_value_id)
        self._tile = tile
        self._node = node

    def append(self, value):
        if not isinstance(value, ConceptValueViewModel):
            value = REGISTER.make(self._tile, self._node, value=value)
        super().append(value)

    def remove(self, value):
        if not isinstance(value, ConceptValueViewModel):
            value = REGISTER.make(self._tile, self._node, value=value)
        super().remove(value)

    def as_tile_data(self):
        return [x.as_tile_data() for x in self]


class RelatedResourceInstanceViewModel(WKRI):
    """Wraps a concept, allowing interrogation.

    Subclasses str, so it can be handled like a string enum, but keeps
    the `.value`, `.lang` and `.text` properties cached, so you can
    find out more.
    """

    @classmethod
    def from_triple(
        cls,
        tile,
        node,
        value: uuid.UUID | str | WKRI | Resource | ResourceInstance | None,
        parent,
        datatype,
        related_prefetch,
    ):
        if value is None:
            raise NotImplementedError()
        resource_instance_id = None
        resource_instance = None
        if isinstance(value, uuid.UUID | str):
            resource_instance_id = value
        else:
            resource_instance = value
        related = cls.create_related(
            parent,
            resource_instance,
            resource_instance_id,
            datatype,
            related_prefetch,
            tile,
            node,
        )
        return related

    def as_tile_data(self):
        raise NotImplementedError()

    @classmethod
    def create_related(
        cls,
        parent_wkri: WKRI,
        resource_instance: WKRI | Resource | ResourceInstance | None,
        resource_instance_id: uuid.UUID | str | None,
        resource_instance_datatype: ResourceInstanceDataType,
        related_prefetch,
        tile,
        node,
    ):
        from .utils import (
            get_well_known_resource_model_by_graph_id,
            attempt_well_known_resource_model,
        )

        _resource_instance: WKRI | None = None

        if not resource_instance:
            if resource_instance_id:
                _resource_instance = attempt_well_known_resource_model(
                    resource_instance_id, related_prefetch=related_prefetch
                )
            else:
                raise RuntimeError("Must pass a resource instance or ID")

        if not isinstance(resource_instance, WKRI):
            wkrm = get_well_known_resource_model_by_graph_id(
                resource_instance.graph_id, default=None
            )
            if wkrm:
                _resource_instance = wkrm.from_resource(resource_instance)
            else:
                raise RuntimeError("Cannot adapt unknown resource model")
        else:
            _resource_instance = resource_instance

        if _resource_instance is None:
            raise RuntimeError("Could not normalize resource instance")

        datum = {}
        datum["wkriFrom"] = parent_wkri
        datum[
            "wkriFromKey"
        ] = node.alias  # FIXME: we should use the ORM key to be consistent
        datum["wkriFromNodeid"] = node.nodeid
        datum["wkriFromTile"] = tile
        datum["datatype"] = resource_instance_datatype

        if (
            _resource_instance._cross_record
            and _resource_instance._cross_record != datum
        ):
            raise NotImplementedError("Cannot currently reparent a resource instance")

        _resource_instance._cross_record = datum

        return _resource_instance

    def get_relationships(self):
        # TODO: nesting
        return [self]


class RelatedResourceInstanceListViewModel(UserList):
    """Wraps a concept list, allowing interrogation.

    Subclasses list, so its members can be handled like a string enum, but keeps
    the `.value`, `.lang` and `.text` properties cached, so you can
    find out more.
    """

    _tile: Tile
    _node: Node
    _resource_instance_list_datatype: BaseDataType

    def __init__(
        self,
        parent_wkri,
        resource_instance_list,
        resource_instance_list_datatype: ResourceInstanceListDataType,
        tile,
        node,
        related_prefetch,
    ):
        self._parent_wkri = parent_wkri
        self._resource_instance_list_datatype = resource_instance_list_datatype
        self._tile = tile
        self._node = node
        self._related_prefetch = related_prefetch
        for resource_instance in resource_instance_list:
            self.append(resource_instance)

    def append(self, item: str | uuid.UUID | Resource | ResourceInstance | WKRI):
        """Add a well-known resource to the list."""

        if isinstance(item, RelatedResourceInstanceViewModel):
            raise NotImplementedError("Cannot currently reparent related resources")

        resource_instance = (
            item if isinstance(item, Resource | ResourceInstance | WKRI) else None
        )
        resource_instance_id = item if isinstance(item, str | uuid.UUID) else None

        value = REGISTER.make(
            self._tile,
            self._node,
            value=(resource_instance or resource_instance_id),
            parent=self._parent_wkri,
            related_prefetch=self._related_prefetch,
        )
        if str(value._cross_record["wkriFrom"]) != str(self._parent_wkri.id):
            raise NotImplementedError("Cannot current reparent related resources")

        return super().append(item)

    def remove(self, value):
        for item in self:
            if value.resourceinstanceid == item.resourceinstanceid:
                value = item
        super().remove(value)

    def get_relationships(self):
        return sum((x.get_relationships() for x in self), [])

    def as_tile_data(self):
        return [x.as_tile_data() for x in self]
