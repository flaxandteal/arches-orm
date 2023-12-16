from typing import Union, Callable, Protocol
import uuid
from functools import lru_cache
from collections import UserList
from collections.abc import Iterable


class ResourceProtocol(Protocol):
    graphid: uuid.UUID
    _cross_record: dict | None = None


class WKRI:
    ...

class ViewModel:
    _parent_pseudo_node = None


class NodeListViewModel(UserList, ViewModel):
    def __init__(self, nodelist):
        self.nodelist = nodelist
        self._parent_pseudo_node = self.nodelist

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

class UserProtocol(Protocol):
    """Provides a standard format for exposing a user."""

    pk: int
    email: str



class UserViewModelMixin(ViewModel):
    """Wraps a user, so that a Django User can be obtained.

    To access the actual user, use `.user`.
    """

    ...


class StringViewModel(str, ViewModel):
    """Wraps a string, allowing language translation.

    Subclasses str, but also allows `.lang("zh")`, etc. to re-translate.
    """

    _value: dict
    _flatten_cb: Callable[[dict, str], str]

    def __new__(cls, value: dict, flatten_cb, language=None):
        display_value = flatten_cb(value, language)
        mystr = super(StringViewModel, cls).__new__(cls, display_value)
        mystr._value = value
        mystr._flatten_cb = flatten_cb
        return mystr

    def lang(self, language):
        return self._flatten_cb(self._value, language)


class ConceptProtocol(Protocol):
    """Minimal representation of an Arches concept."""

    value: str
    language: str


class ConceptValueViewModel(str, ViewModel):
    """Wraps a concept, allowing interrogation.

    Subclasses str, so it can be handled like a string enum, but keeps
    the `.value`, `.lang` and `.text` properties cached, so you can
    find out more.
    """

    _concept_value_id: uuid.UUID
    _concept_value_cb: Callable[[uuid.UUID], ConceptProtocol]

    def __eq__(self, other):
        return self.conceptid == other.conceptid

    def __new__(
        cls,
        concept_value_id: Union[str, uuid.UUID],
        concept_value_cb,
    ):
        _concept_value_id: uuid.UUID = (
            concept_value_id
            if isinstance(concept_value_id, uuid.UUID)
            else uuid.UUID(concept_value_id)
        )
        mystr = super(ConceptValueViewModel, cls).__new__(cls, str(_concept_value_id))
        mystr._concept_value_id = _concept_value_id
        mystr._concept_value_cb = concept_value_cb
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
        return self._concept_value_cb(self._concept_value_id)

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


class ConceptListValueViewModel(UserList, ViewModel):
    """Wraps a concept list, allowing interrogation.

    Subclasses list, so its members can be handled like a string enum, but keeps
    the `.value`, `.lang` and `.text` properties cached, so you can
    find out more.
    """

    def __init__(
        self,
        concept_value_ids: Iterable[str | uuid.UUID],
        make_cb,
    ):
        for concept_value_id in concept_value_ids:
            self.append(concept_value_id)
        self._make_cb = make_cb

    def append(self, value):
        if not isinstance(value, ConceptValueViewModel):
            value = self._make_cb(value)
        super().append(value)

    def remove(self, value):
        if not isinstance(value, ConceptValueViewModel):
            value = self._make_cb(value)
        super().remove(value)


class RelatedResourceInstanceViewModelMixin(ViewModel):
    """Wraps a resource instance.

    Subclasses str, so it can be handled like a string enum, but keeps
    the `.value`, `.lang` and `.text` properties cached, so you can
    find out more.
    """

    def get_relationships(self):
        # TODO: nesting
        return [self]


class RelatedResourceInstanceListViewModel(UserList, ViewModel):
    """Wraps a concept list, allowing interrogation.

    Subclasses list, so its members can be handled like a string enum, but keeps
    the `.value`, `.lang` and `.text` properties cached, so you can
    find out more.
    """

    def __init__(
        self,
        parent_wkri,
        resource_instance_list,
        make_ri_cb,
    ):
        self._parent_wkri = parent_wkri
        self._make_ri_cb = make_ri_cb
        for resource_instance in resource_instance_list:
            self.append(resource_instance)

    def append(self, item: str | uuid.UUID | ResourceProtocol):
        """Add a well-known resource to the list."""

        if isinstance(item, RelatedResourceInstanceViewModelMixin):
            raise NotImplementedError("Cannot currently reparent related resources")

        resource_instance = item if isinstance(item, ResourceProtocol) else None
        resource_instance_id = item if isinstance(item, str | uuid.UUID) else None

        value = self._make_ri_cb(resource_instance or resource_instance_id)
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


class SemanticViewModel(ViewModel):
    """Wraps a semantic tile."""

    _child_keys = None
    _parent_wkri = None
    _child_values = None
    _make_pseudo_node = None

    def __init__(self, parent_wkri, child_keys, values, make_pseudo_node):
        self._child_keys = child_keys
        self._parent_wkri = parent_wkri
        self._child_values = {
            key: value
            for key, value in parent_wkri._values.items()
            if key in child_keys and value is not None
        }

        self._make_pseudo_node = make_pseudo_node

    def get_children(self, direct=None):
        children = [
            value
            for key, value in self._child_values.items()
            if (direct is None or direct == self._child_keys[key]) and value is not None
        ]
        return children

    def __getattr__(self, key):
        if key in self.__dict__:
            return super().__getattr__(key)

        if key not in self._child_keys:
            raise AttributeError("Semantic node does not have this key")

        if key not in self._child_values:
            self._child_values[key] = self._make_pseudo_node(key)
        if isinstance(self._child_values[key], UserList):
            return self._child_values[key].value_list()
        else:
            return self._child_values[key].value

    def __setattr__(self, key, value):
        if key in (
            "_child_keys",
            "_parent_wkri",
            "_child_values",
            "_make_pseudo_node",
            "_parent_pseudo_node",
        ):
            return super().__setattr__(key, value)

        if key not in self._child_keys:
            raise AttributeError("Semantic node does not have this key")

        if key not in self._child_values:
            self._child_values[key] = self._make_pseudo_node(key)
        self._child_values[key].value = value
