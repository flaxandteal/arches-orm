from typing import Callable
from ._base import (
    ViewModel,
)


class UrlViewModel(str, ViewModel):
    """Wraps a string, allowing language translation.

    Subclasses str, but also allows `.lang("zh")`, etc. to re-translate.
    """

    _value: dict[str, str]

    def __new__(cls, value: str, label: str | None=None):
        label = label or value
        mystr = super(UrlViewModel, cls).__new__(cls, value)
        mystr._value = {"href": value, "label": label}
        return mystr

    @property
    def href(self) -> str:
        return self._value["href"]

    @property
    def label(self) -> str:
        return self._value["label"]
