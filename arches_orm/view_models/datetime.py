from __future__ import annotations
from datetime import datetime
from ._base import (
    ViewModel,
)

# TODO: possibly slow, not very clean.
def _add_view_model_class(obj, cls):
    obj.__class__ = cls.__class__(f"{cls.__name__}ViewModel", (cls, ViewModel), {})
    return obj

class DateTimeViewModel(datetime, ViewModel):
    @classmethod
    def parse(cls, value: str | datetime):
        if isinstance(value, str):
            value = datetime.fromisoformat(value)
        return cls(
            value.year,
            value.month,
            value.day,
            hour=value.hour,
            minute=value.minute,
            microsecond=value.microsecond,
            tzinfo=value.tzinfo
        )

    def __new__(cls, *args, **kwargs):
        value = super().__new__(cls, *args, **kwargs)
        value._parent_pseudo_node = None
        # Note; We cannot add ViewModel as a class to datetime (subclass) so
        # isinstance checks for ViewModel will miss this.
        return value
