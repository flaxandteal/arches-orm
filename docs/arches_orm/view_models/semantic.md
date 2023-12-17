# Module arches_orm.view_models.semantic

??? example "View Source"
        from collections import UserList

        from ._base import (

            ViewModel,

        )

        class SemanticViewModel(ViewModel):

            """Wraps a semantic tile."""

            _child_keys = None

            _parent_wkri = None

            _child_values = None

            _make_child = None

            def __init__(self, parent_wkri, child_keys, values, make_child):

                self._child_keys = child_keys

                self._parent_wkri = parent_wkri

                self._child_values = {

                    key: value

                    for key, value in parent_wkri._values.items()

                    if key in child_keys and value is not None

                }

                self._make_child = make_child

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

                    raise AttributeError("Semantic node does not have this key")

                if key not in self._child_values:

                    self._child_values[key] = self._make_child(key)

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

                    self._child_values[key] = self._make_child(key)

                self._child_values[key].value = value

## Classes

### SemanticViewModel

```python3
class SemanticViewModel(
    parent_wkri,
    child_keys,
    values,
    make_child
)
```

Wraps a semantic tile.

??? example "View Source"
        class SemanticViewModel(ViewModel):

            """Wraps a semantic tile."""

            _child_keys = None

            _parent_wkri = None

            _child_values = None

            _make_child = None

            def __init__(self, parent_wkri, child_keys, values, make_child):

                self._child_keys = child_keys

                self._parent_wkri = parent_wkri

                self._child_values = {

                    key: value

                    for key, value in parent_wkri._values.items()

                    if key in child_keys and value is not None

                }

                self._make_child = make_child

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

                    raise AttributeError("Semantic node does not have this key")

                if key not in self._child_values:

                    self._child_values[key] = self._make_child(key)

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

                    self._child_values[key] = self._make_child(key)

                self._child_values[key].value = value

------

#### Ancestors (in MRO)

* arches_orm.view_models._base.ViewModel

#### Methods

    
#### get_children

```python3
def get_children(
    self,
    direct=None
)
```

??? example "View Source"
            def get_children(self, direct=None):

                children = [

                    value

                    for key, value in self._child_values.items()

                    if (direct is None or direct == self._child_keys[key]) and value is not None

                ]

                return children