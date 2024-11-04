from __future__ import annotations

from enum import Enum
from typing import Union, Callable, Protocol, Any
from uuid import UUID
from pathlib import Path
from functools import lru_cache
from collections import UserList
from collections.abc import Iterable
from dataclasses import dataclass, field
from arches_orm.utils import string_to_enum
from rdflib.term import Node
from rdflib.namespace import SKOS
from ._base import (
    ViewModel,
)


DEFAULT_LANGUAGE: str = "en"

class ValueProtocol(Protocol):
    """Minimal representation of an Arches concept."""

    value: str
    language: str

class StaticNode:
    __type__: type[Node] | None = None

@dataclass
class StaticValue(StaticNode):
    """Parallel of the Arches Value model."""

    id: UUID
    value: str
    language: str
    concept_id: UUID | None

@dataclass
class StaticRelationship(StaticNode):
    rdf_resource: str

class StaticPrefLabel(StaticValue):
    __type__: type[Node] = SKOS.prefLabel

class StaticAltLabel(StaticValue):
    __type__: type[Node] = SKOS.altLabel

class StaticRelated(StaticRelationship):
    __type__: type[Node] = SKOS.related

class StaticNarrower(StaticRelationship):
    __type__: type[Node] = SKOS.narrower

class StaticBroader(StaticRelationship):
    __type__: type[Node] = SKOS.broader

class StaticScopeNote(StaticValue):
    __type__: type[Node] = SKOS.scopeNote

@dataclass
class StaticConcept:
    """Minimal representation of an Arches concept."""

    id: UUID
    values: dict[UUID, StaticValue]
    source: Path | None
    _children: list["StaticConcept"] | Callable[[], list["StaticConcept"]]
    identifier: str | None = None
    related: list[StaticRelationship] = field(default_factory=list)
    sort_order: int | None = None
    _title: dict[str | None, StaticValue | None] = field(default_factory=dict)

    @property
    def children(self) -> list["StaticConcept"]:
        """Note that this function will only compute children once."""
        if callable(self._children):
            # Flatten to avoid recalling.
            self._children = self._children()
        return self._children

    def title(self, language: str | None = DEFAULT_LANGUAGE) -> StaticValue | None:
        if language in self._title:
            return self._title[language]

        title = None
        values: list[StaticValue]
        try:
            values = list(value for value in self.values.values() if isinstance(value, StaticPrefLabel))
        except StopIteration:
            try:
                values = list(value for value in self.values.values() if isinstance(value, StaticAltLabel))
            except StopIteration:
                values = []

        if language:
            try:
                title = next(value for value in values if hasattr(value, "language") and value.language == language)
            except StopIteration:
                ...

        if title is None:
            try:
                title = next(iter(self.values.values()))
            except StopIteration:
                ...

        self._title[language] = title
        return title

@dataclass
class StaticConceptScheme(StaticConcept):
    """Minimal representation of a concept scheme.

    For simplicity, this is a subclass of concept.
    """


class CollectionChild:
    _collection_id: UUID | None
    _collection_cb: Callable[[UUID], type[Enum]]

    def __init__(self, collection_id: UUID | None, retrieve_collection_cb: Callable[[UUID], type[Enum]]):
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
    """Wraps a concept value, allowing interrogation.

    Subclasses str, so it can be handled like a string enum, but keeps
    the `.value`, `.lang` and `.text` properties cached, so you can
    find out more.

    Note that, the internal Arches representation of collections seems
    to treat values as the (primary) children - for example,
    `Concept.get_child_collections(...)` returns values and a valueid
    is stored in a tile for a concept node.
    """

    _concept_value_id: UUID
    _concept_value_cb: Callable[[UUID], ValueProtocol]
    _concept_cb: Callable[[UUID], StaticConcept]
    _collection_id: UUID | None
    _collection_cb: Callable[[UUID], type[Enum]]
    _children_cb: Callable[[UUID, str | None], "ConceptValueViewModel"]
    _concept_id: UUID | None

    def __hash__(self):
        return hash(self._concept_value_id)

    def __eq__(self, other):
        if isinstance(other, Enum):
            other = other.value

        # Avoids unnecessarily serializing UUIDs.
        if type(self._concept_value_id) == type(other._concept_value_id):
            return self._concept_value_id == other._concept_value_id

        return str(self._concept_value_id) == str(other._concept_value_id)

    def __init__(self, *args, **kwargs):
        ...

    def __new__(
        cls,
        concept_value_id: Union[str, UUID],
        concept_value_cb: Callable[[UUID], ValueProtocol],
        concept_cb: Callable[[UUID], StaticConcept],
        collection_id: UUID | None,
        retrieve_collection_cb: Callable[[UUID], type[Enum]],
        retrieve_children_cb: Callable[[UUID, str | None], "ConceptValueViewModel"]
    ) -> "ConceptValueViewModel":
        _concept_value_id: UUID = (
            concept_value_id
            if isinstance(concept_value_id, UUID) else
            concept_value_id.value._concept_value_id
            if isinstance(concept_value_id, Enum) else
            concept_value_id._concept_value_id
            if isinstance(concept_value_id, ConceptValueViewModel) else
            UUID(concept_value_id)
        )
        mystr = super(ConceptValueViewModel, cls).__new__(cls, str(_concept_value_id))
        mystr._concept_value_id = _concept_value_id
        mystr._concept_value_cb = concept_value_cb
        mystr._concept_cb = concept_cb
        mystr._collection_id = collection_id
        mystr._collection_cb = retrieve_collection_cb
        mystr._children_cb = retrieve_children_cb
        mystr._concept_id = None
        return mystr

    @property
    def conceptid(self) -> UUID:
        if self._concept_id is not None:
            return self._concept_id
        self._concept_id = self.value.concept_id
        return self._concept_id

    @property
    def concept(self):
        if self.value.concept_id is None:
            return None
        return self._concept_cb(self.value.concept_id)

    @property
    def children(self) -> list[ConceptValueViewModel]:
        children = self._children_cb(self.conceptid, self.lang)
        return children

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
        concept_value_ids: Iterable[str | UUID],
        make_cb: Callable[[UUID], ConceptValueViewModel],
        collection_id: UUID | None,
        retrieve_collection_cb: Callable[[UUID], type[Enum]],
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
