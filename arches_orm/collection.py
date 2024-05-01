from enum import Enum

from .utils import string_to_enum

def make_collection(name: str, collection: list[str]) -> type:
    class classdict(dict):
        _member_names: dict

    values = classdict()
    for entry in collection:
        if hasattr(entry, "_concept_value_id"):
            values[string_to_enum(entry.text)] = entry
    setattr(values, "_member_names", list(values.keys()))
    return type(name, (Enum,), values)
