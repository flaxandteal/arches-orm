from typing import Protocol
from ._base import (
    ViewModel,
)

class UserProtocol(Protocol):
    """Provides a standard format for exposing a user."""

    pk: int
    email: str



class UserViewModelMixin(ViewModel):
    """Wraps a user, so that a Django User can be obtained.

    To access the actual user, use `.user`.
    """

    ...
