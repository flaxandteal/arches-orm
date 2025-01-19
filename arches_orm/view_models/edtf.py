from typing import Callable
from edtf import parse_edtf
from edtf.parser.parser_classes import Date
from ._base import (
    ViewModel,
)


class ExtendedDateViewModel(Date, ViewModel):
    """Wraps a string, allowing language translation.

    Subclasses str, but also allows `.lang("zh")`, etc. to re-translate.
    """

    def __new__(cls, value: str, **config):
        # TODO: use the config!
        edtf = parse_edtf(value)
        return edtf
