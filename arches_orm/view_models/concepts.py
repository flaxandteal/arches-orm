from typing import Union, Callable, Protocol
import uuid
from functools import lru_cache
from collections import UserList
from collections.abc import Iterable
from ._base import (
    ViewModel,
)


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

    def __hash__(self):
        return hash(self._concept_value_id)

    def __eq__(self, other):
        return str(self._concept_value_id) == str(other._concept_value_id)

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
    def conceptid(self):
        return self.value.concept_id

    @property
    def concept(self):
        return self.value.concept

    @property
    @lru_cache
    def value(self):
        return self._concept_value_cb(self._concept_value_id)

    @property
    def text(self):
        return self.value.value

    @property
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
        super().__init__()
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
