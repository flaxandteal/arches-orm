import logging
import slugify
import re
from functools import partial

from .adapter import get_adapter
from .wkrm import get_resource_models_for_adapter

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


def get_well_known_resource_model_by_class_name(
    class_name, default=None, adapter: str | None = None
):
    """Turns a class-name as a string into a well-known resource model wrapper."""
    resource_models = get_resource_models_for_adapter(adapter)["by-class"]
    return resource_models.get(class_name, default)


def get_well_known_resource_model_by_graph_id(
    graphid, default=None, adapter: str | None = None
):
    """Turns a graph into a well-known resource model wrapper, by ID, if known."""
    resource_models_by_graph_id = get_resource_models_for_adapter(adapter)[
        "by-graph-id"
    ]
    return resource_models_by_graph_id.get(str(graphid), default)


def attempt_well_known_resource_model(
    resource_id, from_prefetch=None, adapter=None, **kwargs
):
    """Attempts to find and create a well-known resource from a resource ID

    This is the simplest entry-point if you do not know the model of the resource
    you have. Bear in mind, it will return None if a well-known resource model
    is not matched.
    """

    return get_adapter(adapter).load_from_id(
        resource_id=resource_id, from_prefetch=from_prefetch
    )

def snake(class_name):
    class_name = class_name[0].lower() + class_name[1:]
    if class_name[0] == "_" and class_name[1].isnumeric():
        class_name = class_name[1:]
    class_name = class_name[0] + re.sub("([a-zA-Z])([A-Z])", r"\1_\2", class_name[1:])
    return class_name.lower()


def string_to_enum(string, full=True):
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


def camel(string, studly=False):
    string = ((string[0].upper() if studly else string[0].lower()) + string.replace("_", " ").title()[1:]).replace(" ", "")
    return string
studly = partial(camel, studly=True)

def is_unset(variable):
    if variable is None:
        return True
    try:
        return hash(variable) == hash(None)
    except TypeError:
        ...
    return False
