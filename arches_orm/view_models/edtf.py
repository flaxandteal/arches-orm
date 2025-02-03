from __future__ import annotations
from typing import Callable
from edtf import parse_edtf, text_to_edtf
from edtf.parser.parser_classes import Date, DateAndTime, Interval, UncertainOrApproximate
from edtf.parser.edtf_exceptions import EDTFParseException
from ._base import (
    ViewModel,
)

def make_edtf(value: str, **config):
    # TODO: use the config!
    try:
        edtf = parse_edtf(value)
    except EDTFParseException:
        edtf = parse_edtf(text_to_edtf(value))
    # TODO: possibly slow, not very clean.
    edtf.__class__ = edtf.__class__.__class__(f"Extended{edtf.__class__.__name__}ViewModel", (edtf.__class__, ViewModel), {})
    return edtf
