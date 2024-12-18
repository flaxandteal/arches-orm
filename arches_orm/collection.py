from __future__ import annotations

from enum import Enum
from pathlib import Path
from uuid import UUID
from typing import IO

from rdflib.term import Node
from rdflib.namespace import SKOS

from .utils import string_to_enum, consistent_uuid
from .view_models.concepts import ConceptValueViewModel
from .adapter import Adapter

class CollectionEnum(Enum):
    __original_name__: str = None
    __identifier__: str = None

def make_collection(name: str, collection: list[ConceptValueViewModel], identifier: str | None) -> type[CollectionEnum]:
    values = dict()
    def _get_children(entries: list[ConceptValueViewModel]) -> None:
        for entry in entries:
            if hasattr(entry, "_concept_value_id"):
                values[entry.enum] = entry
            _get_children(entry.children)
    _get_children(collection)
    new_collection = CollectionEnum(string_to_enum(name), values) # type: ignore
    setattr(new_collection, "__original_name__", name)
    setattr(new_collection, "__identifier__", identifier)
    return new_collection

class ReferenceDataManager:
    def __init__(self, adapter: Adapter):
        self.adapter = adapter

    def make_simple_concept(self, namespace: str, value: str | None = None, language: str = "en", children: list[UUID] | list[ConceptValueViewModel] | None = None, scheme: bool = False) -> ConceptValueViewModel:
        """Creates a concept with a consistent set of UUIDs, but depends on namespace+value being globally unique."""

        if value is None:
            value = namespace
        concept_id = consistent_uuid(namespace + "/" + value)
        value_id = consistent_uuid(namespace + "/" + language + "/" + value)
        return self.make_concept(concept_id, {value_id: (language, value, SKOS.prefLabel)}, children=children, scheme=scheme)

    def make_concept(self, concept_id: str | UUID, values: dict[UUID, tuple[str, str, Node]], children: list[UUID] | list[ConceptValueViewModel] | None = None, scheme: bool = False) -> ConceptValueViewModel:
        children_uuids = [child.conceptid if isinstance(child, ConceptValueViewModel) else child for child in (children or [])]
        return self.adapter.make_concept(
            concept_id=concept_id,
            values=values,
            children=children_uuids,
            scheme=scheme
        )

    def concept_to_collection(self, concept: ConceptValueViewModel) -> type[Enum]:
        return self.make_collection(name=concept.text, collection=concept.children)

    def make_collection(self, name: str, collection: list[ConceptValueViewModel]) -> type[Enum]:
        return make_collection(name=name, collection=collection, identifier=None)

    def derive_collection(self, collection_id: str | UUID, include: list[ConceptValueViewModel] | None=None, exclude: list[ConceptValueViewModel] | None=None, language: str | None=None) -> type[Enum]:
        """Note that this method creates a new Enum but does not overwrite the old Collection, and the old version will still be returned from get_collection."""
        if include:
            include_concepts = [inc.conceptid for inc in include]
        else:
            include_concepts = None
        if exclude:
            exclude_concepts = [exc.conceptid for exc in exclude]
        else:
            exclude_concepts = None
        return self.adapter.derive_collection(collection_id, include=include_concepts, exclude=exclude_concepts, language=language)

    def find_collection_by_label(self, title: str, pref_label_only=True) -> type[Enum]:
        return self.adapter.get_collections_by_label(title, pref_label_only)[0]

    def find_concept_by_label(self, title: str, pref_label_only=True) -> ConceptValueViewModel:
        concepts = self.adapter.get_concepts_by_label(title, pref_label_only)
        if len(concepts) == 1:
            return concepts[0]
        elif concepts:
            raise ValueError(f"Multiple collections found for '{title}': {' '.join([str(c) for c in concepts])}")
        else:
            raise KeyError(f"Collection {title} not found")

    def find_collection_by_label(self, title: str, pref_label_only=True) -> type[Enum]:
        collections = self.adapter.get_collections_by_label(title, pref_label_only)
        if len(collections) == 1:
            return collections[0]
        elif collections:
            raise ValueError(f"Multiple collections found for '{title}': {' '.join([str(c) for c in collections])}")
        else:
            raise KeyError(f"Collection {title} not found")

    def get_collection(self, collection_id: str | UUID) -> type[Enum]:
        return self.adapter.get_collection(collection_id)

    def get_concept(self, concept_id: str | UUID) -> ConceptValueViewModel:
        return self.adapter.retrieve_concept_value(concept_id)

    def save_concept(self, concept: ConceptValueViewModel, output_file: Path | None) -> None:
        return self.adapter.save_concept(concept, output_file)

    def export_collection(self, concept: ConceptValueViewModel, output_file: Path | IO) -> None:
        return self.adapter.export_collection(concept, output_file)

    def update_collections(self, concept: ConceptValueViewModel, output_file: Path) -> None:
        return self.adapter.update_collections(concept, output_file)
