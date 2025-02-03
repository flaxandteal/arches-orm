from __future__ import annotations
from typing import Callable
from edtf import parse_edtf, text_to_edtf
from edtf.parser.parser_classes import Date, DateAndTime, Interval
from edtf.parser.edtf_exceptions import EDTFParseException
from ._base import (
    ViewModel,
)

def _make_edtf(value: str, **config):
    # TODO: use the config!
    try:
        edtf = parse_edtf(value)
    except EDTFParseException:
        edtf = parse_edtf(text_to_edtf(value))
    if isinstance(edtf, Date):
        return ExtendedDateViewModel(edtf)
    elif isinstance(edtf, DateAndTime):
        return ExtendedDateAndTimeViewModel(edtf)
    elif isinstance(edtf, Interval):
        return ExtendedIntervalViewModel(edtf)
    raise RuntimeError(f"Unrecognised EDTF class {type(edtf)} for {edtf}")

# TODO: possibly slow, not very clean.
def _add_view_model_class(obj, cls):
    obj.__class__ = cls.__class__(f"Extended{cls.__name__}ViewModel", (cls, ViewModel), {})
    return obj

class ExtendedDateAndTimeViewModel(DateAndTime, ViewModel):
    def __new__(cls, value: str | DateAndTime, **config):
        if isinstance(value, str):
            return _make_edtf(value, **config)
        return _add_view_model_class(value, DateAndTime)

class ExtendedDateViewModel(Date, ViewModel):
    def __new__(cls, value: str | Date, **config):
        if isinstance(value, str):
            return _make_edtf(value, **config)
        return _add_view_model_class(value, Date)

class ExtendedIntervalViewModel(Interval, ViewModel):
    def __new__(cls, value: str | Interval, **config):
        if isinstance(value, str):
            return _make_edtf(value, **config)
        return _add_view_model_class(value, Interval)
