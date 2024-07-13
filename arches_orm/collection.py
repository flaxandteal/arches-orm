from enum import Enum
from pathlib import Path
from uuid import UUID

from .utils import string_to_enum, consistent_uuid
from .view_models.concepts import ConceptValueViewModel
from .adapter import Adapter

class CollectionEnum(Enum):
    __original_name__: str = None
    __identifier__: str = None

def make_collection(name: str, collection: list[ConceptValueViewModel], identifier: str | None) -> type[CollectionEnum]:
    values = dict()
    for entry in collection:
        if hasattr(entry, "_concept_value_id"):
            values[entry.enum] = entry
    new_collection = CollectionEnum(string_to_enum(name), values) # type: ignore
    setattr(new_collection, "__original_name__", name)
    setattr(new_collection, "__identifier__", identifier)
    return new_collection

class ReferenceDataManager:
    def __init__(self, adapter: Adapter):
        self.adapter = adapter

    def make_simple_concept(self, namespace: str, value: str | None = None, language: str = "en", children: list[UUID] | list[ConceptValueViewModel] | None = None) -> ConceptValueViewModel:
        """Creates a concept with a consistent set of UUIDs, but depends on namespace+value being globally unique."""

        if value is None:
            value = namespace
        concept_id = consistent_uuid(namespace + "/" + value)
        value_id = consistent_uuid(namespace + "/" + language + "/" + value)
        return self.make_concept(concept_id, {value_id: (language, value)}, children=children)

    def make_concept(self, concept_id: str | UUID, values: dict[UUID, tuple[str, str]], children: list[UUID] | list[ConceptValueViewModel] | None = None) -> ConceptValueViewModel:
        children_uuids = [child.conceptid if isinstance(child, ConceptValueViewModel) else child for child in (children or [])]
        return self.adapter.make_concept(
            concept_id=concept_id,
            values=values,
            children=children_uuids
        )

    def concept_to_collection(self, concept: ConceptValueViewModel) -> type[Enum]:
        return self.make_collection(name=concept.text, collection=concept.children)

    def make_collection(self, name: str, collection: list[ConceptValueViewModel]) -> type[Enum]:
        return make_collection(name=name, collection=collection, identifier=None)

    def save_concept(self, concept: ConceptValueViewModel, output_file: Path | None) -> None:
        return self.adapter.save_concept(concept, output_file)

    def update_collections(self, concept: ConceptValueViewModel, output_file: Path) -> None:
        return self.adapter.update_collections(concept, output_file)
