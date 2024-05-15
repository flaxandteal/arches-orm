from typing import Protocol
from ._base import (
    ViewModel,
)


class GroupProtocol(Protocol):
    """Provides a standard format for exposing a (Django) group."""

    pk: int
    name: str


class GroupViewModelMixin(ViewModel):
    """Wraps a group, so that a Django Group can be obtained.

    To access the actual group, use `.group`.
    """

    ...
