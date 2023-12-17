from collections.abc import Iterable
from collections import UserList
from ._base import (
    ViewModel,
)


class SemanticViewModel(ViewModel):
    """Wraps a semantic tile."""

    _child_keys = None
    _parent_wkri = None
    _make_child = None

    def __init__(self, parent_wkri, child_keys, values, make_child):
        self._child_keys = child_keys
        self._parent_wkri = parent_wkri
        self._make_child = make_child

    @property
    def _child_values(self):
        return {
            key: value
            for key, value in self._parent_wkri._values.items()
            if key in self._child_keys and value is not None
        }

    def get_children(self, direct=None):
        children = [
            value
            for key, value in self._child_values.items()
            if (direct is None or direct == self._child_keys[key]) and value is not None
        ]
        return children

    def __getattr__(self, key):
        if key in self.__dict__:
            return super().__getattr__(key)

        if key not in self._child_keys:
            raise AttributeError(f"Semantic node does not have this key: {key}")

        if key not in self._child_values:
            value = self._make_child(key)
            if not isinstance(value, Iterable):
                value = None
            self._parent_wkri._values[key] = value
            return value
        if isinstance(self._child_values[key], UserList):
            return self._child_values[key].value_list()
        else:
            return self._child_values[key].value

    def __setattr__(self, key, value):
        if key in (
            "_child_keys",
            "_parent_wkri",
            "_child_values",
            "_make_child",
            "_parent_pseudo_node",
        ):
            return super().__setattr__(key, value)

        if key not in self._child_keys:
            raise AttributeError("Semantic node does not have this key")

        if key not in self._child_values:
            self._parent_wkri._values[key] = self._make_child(key)
        self._parent_wkri._values[key].value = value
