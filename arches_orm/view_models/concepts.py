from enum import Enum
from typing import Union, Callable, Protocol, Any
import uuid
from functools import lru_cache
from collections import UserList
from collections.abc import Iterable
from arches_orm.utils import string_to_enum
from ._base import (
    ViewModel,
)


class ValueProtocol(Protocol):
    """Minimal representation of an Arches concept."""

    value: str
    language: str


class CollectionChild:
    _collection_id: uuid.UUID | None
    _collection_cb: Callable[[uuid.UUID], type[Enum]]

    def __init__(self, collection_id: uuid.UUID | None, retrieve_collection_cb: Callable[[uuid.UUID], type[Enum]]):
        self._collection_id = collection_id
        self._collection_cb = retrieve_collection_cb

    @property
    def __collection__(self) -> type[Enum] | None:
        if self._collection_id is None:
            return None
        return self._collection_cb(self._collection_id)

class EmptyConceptValueViewModel(CollectionChild, ViewModel):
    def __bool__(self) -> bool:
        return False

    def __hash__(self) -> int:
        return hash(None)

    def __eq__(self, other: Any) -> bool:
        return other is None or isinstance(other, EmptyConceptValueViewModel)

class ConceptValueViewModel(str, CollectionChild, ViewModel):
    """Wraps a concept, allowing interrogation.

    Subclasses str, so it can be handled like a string enum, but keeps
    the `.value`, `.lang` and `.text` properties cached, so you can
    find out more.
    """

    _concept_value_id: uuid.UUID
    _concept_value_cb: Callable[[uuid.UUID], ValueProtocol]
    _collection_id: uuid.UUID | None
    _collection_cb: Callable[[uuid.UUID], type[Enum]]
    _children_cb: Callable[[uuid.UUID, str | None], "ConceptValueViewModel"]

    def __hash__(self):
        return hash(self._concept_value_id)

    def __eq__(self, other):
        if isinstance(other, Enum):
            other = other.value
        return str(self._concept_value_id) == str(other._concept_value_id)

    def __init__(self, *args, **kwargs):
        ...

    def __new__(
        cls,
        concept_value_id: Union[str, uuid.UUID],
        concept_value_cb: Callable[[uuid.UUID], ValueProtocol],
        collection_id: uuid.UUID | None,
        retrieve_collection_cb: Callable[[uuid.UUID], type[Enum]],
        retrieve_children_cb: Callable[[uuid.UUID, str | None], "ConceptValueViewModel"]
    ) -> "ConceptValueViewModel":
        _concept_value_id: uuid.UUID = (
            concept_value_id
            if isinstance(concept_value_id, uuid.UUID) else
            concept_value_id.value._concept_value_id
            if isinstance(concept_value_id, Enum) else
            concept_value_id._concept_value_id
            if isinstance(concept_value_id, ConceptValueViewModel) else
            uuid.UUID(concept_value_id)
        )
        mystr = super(ConceptValueViewModel, cls).__new__(cls, str(_concept_value_id))
        mystr._concept_value_id = _concept_value_id
        mystr._concept_value_cb = concept_value_cb
        mystr._collection_id = collection_id
        mystr._collection_cb = retrieve_collection_cb
        mystr._children_cb = retrieve_children_cb
        return mystr

    @property
    def conceptid(self):
        return self.value.concept_id

    @property
    def concept(self):
        return self.value.concept

    @property
    def children(self):
        return self._children_cb(self.conceptid, self.lang)

    @property
    @lru_cache
    def value(self):
        return self._concept_value_cb(self._concept_value_id)

    @property
    def text(self):
        return self.value.value

    @property
    def enum(self):
        return string_to_enum(self.text)

    @property
    def lang(self):
        return self.value.language

    def __str__(self):
        return self.text

    def __repr__(self):
        return f"{self.value.concept_id}>{self._concept_value_id}[{self.text}]"


class ConceptListValueViewModel(UserList[ConceptValueViewModel], ViewModel, CollectionChild):
    """Wraps a concept list, allowing interrogation.

    Subclasses list, so its members can be handled like a string enum, but keeps
    the `.value`, `.lang` and `.text` properties cached, so you can
    find out more.
    """

    def __init__(
        self,
        concept_value_ids: Iterable[str | uuid.UUID],
        make_cb: Callable[[uuid.UUID], ConceptValueViewModel],
        collection_id: uuid.UUID | None,
        retrieve_collection_cb: Callable[[uuid.UUID], type[Enum]],
    ):
        UserList.__init__(self)
        CollectionChild.__init__(self, collection_id, retrieve_collection_cb)
        self._make_cb = make_cb
        self._serialize_entries = {}
        for concept_value_id in concept_value_ids:
            self.append(concept_value_id)

    def append(self, value):
        if not isinstance(value, ConceptValueViewModel):
            value = self._make_cb(value)
        super().append(value)

    def remove(self, value):
        if not isinstance(value, ConceptValueViewModel):
            value = self._make_cb(value)
        super().remove(value)
