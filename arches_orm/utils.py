import logging
import enum
import uuid
import hashlib
import slugify
import re
from functools import partial
from typing import Any

logger = logging.getLogger(__name__)

_SYMBOL_NAMES = {
    "+": "plus",
    "&": "and",
    "-": "dash",
    "@": "at",
    "#": "hash",
    "%": "percent",
    "*": "star",
    "(": " ",
    ")": " ",
    "?": "q",
    "/": "or",
    "\"": " ",
    "'": " ",
    ":": " ",
    ";": " ",
    ",": " ",
    "£": "GBP",
    "$": "Dlr", # many common dollar types...
    "€": "EUR",
}

# Has to be here so it can be populated before the enum is created.
_CUSTOM_DATATYPES: dict[str, str] | None = {
}

def add_custom_datatype(key: str, value: str, collects_multiple_values: bool=False) -> None:
    if _CUSTOM_DATATYPES is None:
        raise RuntimeError("Cannot add custom datatypes after initialization complete")
    _CUSTOM_DATATYPES[key] = (value, collects_multiple_values)


class StandardDataTypeNames(enum.Enum):
    SEMANTIC = "semantic"
    STRING = "string"
    CONCEPT = "concept"
    CONCEPT_LIST = "concept-list"
    RESOURCE_INSTANCE = "resource-instance"
    RESOURCE_INSTANCE_LIST = "resource-instance-list"
    GEOJSON_FEATURE_COLLECTION = "geojson-feature-collection"
    EDTF = "edtf"
    FILE_LIST = "file-list"
    USER = "user"
    BOOLEAN  = "boolean"
    NUMBER  = "number"
    DATE  = "date"
    URL = "url"
    DOMAIN_VALUE = "domain-value"
    NODE_VALUE = "node-value"
    BNGCENTREPOINT = "bngcentrepoint"
    DOMAIN_VALUE_LIST = "domain-value-list"
    DJANGO_GROUP = "django-group"

def snake(class_name):
    class_name = class_name[0].lower() + class_name[1:]
    if class_name[0] == "_" and class_name[1].isnumeric():
        class_name = class_name[1:]
    class_name = class_name[0] + re.sub("([a-zA-Z])([A-Z])", r"\1_\2", class_name[1:])
    return class_name.lower()


def string_to_enum(string: str, full: bool=True) -> str:
    if not string:
        return ""
    for sym, word in _SYMBOL_NAMES.items():
        if sym in string:
            string = (f" {word} " if word.strip() else word).join([string_to_enum(w, full=False).strip() for w in string.split(sym)])
    string = string.strip()
    string = slugify.slugify(string.replace(" ", "-")).replace("-", " ")
    if full:
        if len(string) == 1 and string[0].isupper():
            string += "_"
        if string[0].isnumeric():
            string = "_" + string
        string = studly(string)
    return string


def camel(string: str, studly: bool=False) -> str:
    string = ((string[0].upper() if studly else string[0].lower()) + string.replace("_", " ").title()[1:]).replace(" ", "")
    return string
studly = partial(camel, studly=True)

def is_unset(variable: Any, unavailable: bool=True) -> bool:
    from arches_orm.view_models._base import UnavailableViewModel

    if variable is None:
        return True
    if isinstance(variable, UnavailableViewModel):
        return unavailable
    try:
        return hash(variable) == hash(None)
    except TypeError:
        ...
    return False

def consistent_uuid(string: str) -> uuid.UUID:
    hsh = hashlib.md5()
    hsh.update(string.encode("utf-8"))
    return uuid.UUID(hsh.hexdigest())
