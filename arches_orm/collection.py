from enum import Enum
from collections import UserDict

from .view_models.concepts import ConceptValueViewModel
from .utils import string_to_enum
from typing import cast

def make_collection(name: str, concept: ConceptValueViewModel, collection: list[ConceptValueViewModel]) -> type[Enum]:
    values = dict()
    for entry in collection:
        if hasattr(entry, "_concept_value_id"):
            values[entry.enum] = entry
    new_collection = Enum(name, values) # type: ignore
    return new_collection
