from enum import Enum

from .utils import string_to_enum
from .view_models.concepts import ConceptValueViewModel

def make_collection(name: str, concept: ConceptValueViewModel, collection: list[ConceptValueViewModel]) -> type[Enum]:
    values = dict()
    for entry in collection:
        if hasattr(entry, "_concept_value_id"):
            values[entry.enum] = entry
    new_collection = Enum(string_to_enum(name), values) # type: ignore
    setattr(new_collection, "__original_name__", name)
    return new_collection
