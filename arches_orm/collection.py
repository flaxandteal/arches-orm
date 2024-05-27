from enum import Enum

from .view_models.concepts import ConceptValueViewModel

def make_collection(name: str, concept: ConceptValueViewModel, collection: list[ConceptValueViewModel]) -> type[Enum]:
    values = dict()
    for entry in collection:
        if hasattr(entry, "_concept_value_id"):
            values[entry.enum] = entry
    new_collection = Enum(name, values) # type: ignore
    return new_collection
