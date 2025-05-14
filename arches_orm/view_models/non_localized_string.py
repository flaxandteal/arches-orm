from typing import Callable
from ._base import (
    ViewModel,
)


class NonLocalizedStringViewModel(str, ViewModel):
    """Wraps a string, allowing language translation.

    Subclasses str, but also allows `.lang("zh")`, etc. to re-translate.
    """

    def __new__(cls, value: str):
        mystr = super(NonLocalizedStringViewModel, cls).__new__(cls, value)
        return mystr
