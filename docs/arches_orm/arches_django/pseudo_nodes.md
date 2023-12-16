# Module arches_orm.arches_django.pseudo_nodes

??? example "View Source"
        from arches.app.models.tile import Tile as TileProxyModel

        from collections import UserList

        from arches_orm.view_models import ViewModel, NodeListViewModel

        from .datatypes import get_view_model_for_datatype

        class PseudoNodeList(UserList):

            def __init__(self, node, parent):

                super().__init__()

                self.node = node

                self.parent = parent

            def value_list(self):

                return NodeListViewModel(self)

            def get_tile(self):

                for pseudo_node in self:

                    pseudo_node.get_tile()

                return None

            def __iadd__(self, other):

                other_pn = [

                    self.parent._make_pseudo_node(

                        self.node.alias,

                        single=True,

                    )

                    if not isinstance(item, PseudoNodeValue)

                    else item

                    for item in other

                ]

                super().__iadd__(other_pn)

            def append(self, item=None):

                if not isinstance(item, PseudoNodeValue):

                    value = self.parent._make_pseudo_node(

                        self.node.alias,

                        single=True,

                    )

                    if item is not None:

                        value.value = item

                    item = value

                super().append(item)

                return item.value

            def get_relationships(self):

                return []

            def get_children(self, direct=None):

                return self

        

        class PseudoNodeValue:

            _value_loaded = False

            _value = None

            def __init__(self, node, tile=None, value=None, parent=None, child_nodes=None):

                self.node = node

                self.tile = tile

                if "Model" in str(self.tile.__class__):

                    raise RuntimeError()

                self._parent = parent

                self._child_nodes = child_nodes

                self._value = value

            def __str__(self):

                return f"{{{self.value}}}"

            def __repr__(self):

                return str(self)

            def get_relationships(self):

                try:

                    return self.value.get_relationships() if self.value else []

                except AttributeError:

                    return []

            def get_tile(self):

                self._update_value()

                if self._as_tile_data:

                    tile_value = self._as_tile_data(self._value)

                else:

                    tile_value = self._value

                self.tile.data[

                    str(self.node.nodeid)

                ] = tile_value  # TODO: ensure this works for any value

                return self.tile if self.node.is_collector else None

            def _update_value(self):

                if not self.tile:

                    if not self.node:

                        raise RuntimeError("Empty tile")

                    self.tile = TileProxyModel(

                        nodegroup_id=self.node.nodegroup_id, tileid=None, data={}

                    )

                if not self._value_loaded:

                    if self.tile.data is not None and str(self.node.nodeid) in self.tile.data:

                        data = self.tile.data[str(self.node.nodeid)]

                    else:

                        data = self._value

                    self._value, self._as_tile_data = get_view_model_for_datatype(

                        self.tile,

                        self.node,

                        value=data,

                        parent=self._parent,

                        child_nodes=self._child_nodes,

                    )

                    if self._value is not None:

                        self._value._parent_pseudo_node = self

                    if self._value is not None:

                        self._value_loaded = True

            @property

            def value(self):

                self._update_value()

                return self._value

            @value.setter

            def value(self, value):

                if not isinstance(value, ViewModel):

                    value, self._as_tile_data = get_view_model_for_datatype(

                        self.tile,

                        self.node,

                        value=value,

                        parent=self._parent,

                        child_nodes=self._child_nodes,

                    )

                self._value = value

                self._value_loaded = True

            def __len__(self):

                return len(self.get_children())

            def get_children(self, direct=None):

                if self.value:

                    try:

                        return self.value.get_children(direct=direct)

                    except AttributeError:

                        ...

                return []

## Classes

### PseudoNodeList

```python3
class PseudoNodeList(
    node,
    parent
)
```

A more or less complete user-defined wrapper around list objects.

??? example "View Source"
        class PseudoNodeList(UserList):

            def __init__(self, node, parent):

                super().__init__()

                self.node = node

                self.parent = parent

            def value_list(self):

                return NodeListViewModel(self)

            def get_tile(self):

                for pseudo_node in self:

                    pseudo_node.get_tile()

                return None

            def __iadd__(self, other):

                other_pn = [

                    self.parent._make_pseudo_node(

                        self.node.alias,

                        single=True,

                    )

                    if not isinstance(item, PseudoNodeValue)

                    else item

                    for item in other

                ]

                super().__iadd__(other_pn)

            def append(self, item=None):

                if not isinstance(item, PseudoNodeValue):

                    value = self.parent._make_pseudo_node(

                        self.node.alias,

                        single=True,

                    )

                    if item is not None:

                        value.value = item

                    item = value

                super().append(item)

                return item.value

            def get_relationships(self):

                return []

            def get_children(self, direct=None):

                return self

------

#### Ancestors (in MRO)

* collections.UserList
* collections.abc.MutableSequence
* collections.abc.Sequence
* collections.abc.Reversible
* collections.abc.Collection
* collections.abc.Sized
* collections.abc.Iterable
* collections.abc.Container

#### Methods

    
#### append

```python3
def append(
    self,
    item=None
)
```

S.append(value) -- append value to the end of the sequence

??? example "View Source"
            def append(self, item=None):

                if not isinstance(item, PseudoNodeValue):

                    value = self.parent._make_pseudo_node(

                        self.node.alias,

                        single=True,

                    )

                    if item is not None:

                        value.value = item

                    item = value

                super().append(item)

                return item.value

    
#### clear

```python3
def clear(
    self
)
```

S.clear() -> None -- remove all items from S

??? example "View Source"
            def clear(self):

                self.data.clear()

    
#### copy

```python3
def copy(
    self
)
```

??? example "View Source"
            def copy(self):

                return self.__class__(self)

    
#### count

```python3
def count(
    self,
    item
)
```

S.count(value) -> integer -- return number of occurrences of value

??? example "View Source"
            def count(self, item):

                return self.data.count(item)

    
#### extend

```python3
def extend(
    self,
    other
)
```

S.extend(iterable) -- extend sequence by appending elements from the iterable

??? example "View Source"
            def extend(self, other):

                if isinstance(other, UserList):

                    self.data.extend(other.data)

                else:

                    self.data.extend(other)

    
#### get_children

```python3
def get_children(
    self,
    direct=None
)
```

??? example "View Source"
            def get_children(self, direct=None):

                return self

    
#### get_relationships

```python3
def get_relationships(
    self
)
```

??? example "View Source"
            def get_relationships(self):

                return []

    
#### get_tile

```python3
def get_tile(
    self
)
```

??? example "View Source"
            def get_tile(self):

                for pseudo_node in self:

                    pseudo_node.get_tile()

                return None

    
#### index

```python3
def index(
    self,
    item,
    *args
)
```

S.index(value, [start, [stop]]) -> integer -- return first index of value.

Raises ValueError if the value is not present.

Supporting start and stop arguments is optional, but
recommended.

??? example "View Source"
            def index(self, item, *args):

                return self.data.index(item, *args)

    
#### insert

```python3
def insert(
    self,
    i,
    item
)
```

S.insert(index, value) -- insert value before index

??? example "View Source"
            def insert(self, i, item):

                self.data.insert(i, item)

    
#### pop

```python3
def pop(
    self,
    i=-1
)
```

S.pop([index]) -> item -- remove and return item at index (default last).

Raise IndexError if list is empty or index is out of range.

??? example "View Source"
            def pop(self, i=-1):

                return self.data.pop(i)

    
#### remove

```python3
def remove(
    self,
    item
)
```

S.remove(value) -- remove first occurrence of value.

Raise ValueError if the value is not present.

??? example "View Source"
            def remove(self, item):

                self.data.remove(item)

    
#### reverse

```python3
def reverse(
    self
)
```

S.reverse() -- reverse *IN PLACE*

??? example "View Source"
            def reverse(self):

                self.data.reverse()

    
#### sort

```python3
def sort(
    self,
    /,
    *args,
    **kwds
)
```

??? example "View Source"
            def sort(self, /, *args, **kwds):

                self.data.sort(*args, **kwds)

    
#### value_list

```python3
def value_list(
    self
)
```

??? example "View Source"
            def value_list(self):

                return NodeListViewModel(self)

### PseudoNodeValue

```python3
class PseudoNodeValue(
    node,
    tile=None,
    value=None,
    parent=None,
    child_nodes=None
)
```

??? example "View Source"
        class PseudoNodeValue:

            _value_loaded = False

            _value = None

            def __init__(self, node, tile=None, value=None, parent=None, child_nodes=None):

                self.node = node

                self.tile = tile

                if "Model" in str(self.tile.__class__):

                    raise RuntimeError()

                self._parent = parent

                self._child_nodes = child_nodes

                self._value = value

            def __str__(self):

                return f"{{{self.value}}}"

            def __repr__(self):

                return str(self)

            def get_relationships(self):

                try:

                    return self.value.get_relationships() if self.value else []

                except AttributeError:

                    return []

            def get_tile(self):

                self._update_value()

                if self._as_tile_data:

                    tile_value = self._as_tile_data(self._value)

                else:

                    tile_value = self._value

                self.tile.data[

                    str(self.node.nodeid)

                ] = tile_value  # TODO: ensure this works for any value

                return self.tile if self.node.is_collector else None

            def _update_value(self):

                if not self.tile:

                    if not self.node:

                        raise RuntimeError("Empty tile")

                    self.tile = TileProxyModel(

                        nodegroup_id=self.node.nodegroup_id, tileid=None, data={}

                    )

                if not self._value_loaded:

                    if self.tile.data is not None and str(self.node.nodeid) in self.tile.data:

                        data = self.tile.data[str(self.node.nodeid)]

                    else:

                        data = self._value

                    self._value, self._as_tile_data = get_view_model_for_datatype(

                        self.tile,

                        self.node,

                        value=data,

                        parent=self._parent,

                        child_nodes=self._child_nodes,

                    )

                    if self._value is not None:

                        self._value._parent_pseudo_node = self

                    if self._value is not None:

                        self._value_loaded = True

            @property

            def value(self):

                self._update_value()

                return self._value

            @value.setter

            def value(self, value):

                if not isinstance(value, ViewModel):

                    value, self._as_tile_data = get_view_model_for_datatype(

                        self.tile,

                        self.node,

                        value=value,

                        parent=self._parent,

                        child_nodes=self._child_nodes,

                    )

                self._value = value

                self._value_loaded = True

            def __len__(self):

                return len(self.get_children())

            def get_children(self, direct=None):

                if self.value:

                    try:

                        return self.value.get_children(direct=direct)

                    except AttributeError:

                        ...

                return []

------

#### Instance variables

```python3
value
```

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

                if self.value:

                    try:

                        return self.value.get_children(direct=direct)

                    except AttributeError:

                        ...

                return []

    
#### get_relationships

```python3
def get_relationships(
    self
)
```

??? example "View Source"
            def get_relationships(self):

                try:

                    return self.value.get_relationships() if self.value else []

                except AttributeError:

                    return []

    
#### get_tile

```python3
def get_tile(
    self
)
```

??? example "View Source"
            def get_tile(self):

                self._update_value()

                if self._as_tile_data:

                    tile_value = self._as_tile_data(self._value)

                else:

                    tile_value = self._value

                self.tile.data[

                    str(self.node.nodeid)

                ] = tile_value  # TODO: ensure this works for any value

                return self.tile if self.node.is_collector else None