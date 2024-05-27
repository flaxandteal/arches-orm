from typing import Mapping
from ._base import (
    ViewModel,
)


class SemanticViewModel(ViewModel, Mapping[str, ViewModel]):
    """Wraps a semantic tile."""

    _child_keys = None
    _parent_wkri = None
    _make_child = None
    _get_child_values = None
    _child_values = None

    def __init__(self, parent_wkri, child_keys, make_child, get_child_values):
        self._child_keys = child_keys
        self._child_values = {}
        self._parent_wkri = parent_wkri
        self._make_child = make_child
        self._get_child_values = get_child_values

    def __getitem__(self, item):
        return getattr(self, item)

    def __len__(self):
        return len(self._child_keys)

    def __iter__(self):
        return iter(self._child_keys)

    def update(self, values):
        for key, value in values.items():
            setattr(self, key, value)

    def get_child_types(self):
        return {
            key: self._get_child_value(key)
            for key in self._child_keys
        }

    def get_children(self, direct=None):
        items = dict(self._get_child_values(self))
        items.update(self._child_values)
        children = [
            value
            for key, value in items.items()
            if (direct is None or direct == self._child_keys[key]) and value is not None
        ]
        return children

    def __getattr__(self, key):
        if key in self.__dict__:
            return super().__getattr__(key)

        child_value = self._get_child_value(key)
        return child_value.value

    def _get_child_value(self, key):
        if key not in self._child_keys:
            raise AttributeError(f"Semantic node does not have this key: {key}")

        if key not in self._child_values:
            if (child := self._get_child_values(self).get(key)) is None:
                child = self._make_child(key)
            self._child_values[key] = child
            child._parent_node = self
        return self._child_values[key]

    def __setattr__(self, key, value):
        if key in (
            "_child_keys",
            "_parent_wkri",
            "_child_values",
            "_make_child",
            "_parent_pseudo_node",
            "_get_child_values",
        ):
            return super().__setattr__(key, value)

        if key not in self._child_keys:
            raise AttributeError(f"Semantic node does not have this key: {key}")

        if key not in self._child_values:
            if key not in self._get_child_values(self):
                child = self._make_child(key)
            else:
                child = self._get_child_values(self)[key]
            self._child_values[key] = child
            child._parent_node = self
        self._child_values[key].value = value
