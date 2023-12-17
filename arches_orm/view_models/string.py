from typing import Callable
from ._base import (
    ViewModel,
)


class StringViewModel(str, ViewModel):
    """Wraps a string, allowing language translation.

    Subclasses str, but also allows `.lang("zh")`, etc. to re-translate.
    """

    _value: dict
    _flatten_cb: Callable[[dict, str], str]

    def __new__(cls, value: dict, flatten_cb, language=None):
        display_value = flatten_cb(value, language)
        mystr = super(StringViewModel, cls).__new__(cls, display_value)
        mystr._value = value
        mystr._flatten_cb = flatten_cb
        return mystr

    def lang(self, language):
        return self._flatten_cb(self._value, language)
