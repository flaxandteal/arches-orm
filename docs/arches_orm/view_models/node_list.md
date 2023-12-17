# Module arches_orm.view_models.node_list

??? example "View Source"
        from collections import UserList

        from ._base import (

            ViewModel,

        )

        class NodeListViewModel(UserList, ViewModel):

            def __init__(self, nodelist):

                self.nodelist = nodelist

                self._parent_pseudo_node = self.nodelist

            @property

            def data(self):

                return [node.value for node in self.nodelist]

            def append(self, item=None):

                value = self.nodelist.append(item)

                return value

            def extend(self, other):

                self.nodelist.extend(other)

            def sort(self, /, *args, **kwds):

                self.nodelist.sort(*args, **kwds)

            def reverse(self):

                self.nodelist.reverse()

            def clear(self):

                self.nodelist.clear()

            def remove(self, item):

                self.nodelist.remove(item)

            def pop(self):

                item = self.nodelist.pop()

                return item.value

            def insert(self, i, item):

                value = self.nodelist.insert(i, item)

                return value

            def __setitem__(self, i, item):

                self.nodelist[i] = item

            def __delitem__(self, i):

                del self.nodelist[i]

            def __iadd__(self, other):

                self.nodelist += other

## Classes

### NodeListViewModel

```python3
class NodeListViewModel(
    nodelist
)
```

A more or less complete user-defined wrapper around list objects.

??? example "View Source"
        class NodeListViewModel(UserList, ViewModel):

            def __init__(self, nodelist):

                self.nodelist = nodelist

                self._parent_pseudo_node = self.nodelist

            @property

            def data(self):

                return [node.value for node in self.nodelist]

            def append(self, item=None):

                value = self.nodelist.append(item)

                return value

            def extend(self, other):

                self.nodelist.extend(other)

            def sort(self, /, *args, **kwds):

                self.nodelist.sort(*args, **kwds)

            def reverse(self):

                self.nodelist.reverse()

            def clear(self):

                self.nodelist.clear()

            def remove(self, item):

                self.nodelist.remove(item)

            def pop(self):

                item = self.nodelist.pop()

                return item.value

            def insert(self, i, item):

                value = self.nodelist.insert(i, item)

                return value

            def __setitem__(self, i, item):

                self.nodelist[i] = item

            def __delitem__(self, i):

                del self.nodelist[i]

            def __iadd__(self, other):

                self.nodelist += other

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
* arches_orm.view_models._base.ViewModel

#### Instance variables

```python3
data
```

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

                value = self.nodelist.append(item)

                return value

    
#### clear

```python3
def clear(
    self
)
```

S.clear() -> None -- remove all items from S

??? example "View Source"
            def clear(self):

                self.nodelist.clear()

    
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

                self.nodelist.extend(other)

    
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

                value = self.nodelist.insert(i, item)

                return value

    
#### pop

```python3
def pop(
    self
)
```

S.pop([index]) -> item -- remove and return item at index (default last).

Raise IndexError if list is empty or index is out of range.

??? example "View Source"
            def pop(self):

                item = self.nodelist.pop()

                return item.value

    
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

                self.nodelist.remove(item)

    
#### reverse

```python3
def reverse(
    self
)
```

S.reverse() -- reverse *IN PLACE*

??? example "View Source"
            def reverse(self):

                self.nodelist.reverse()

    
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

                self.nodelist.sort(*args, **kwds)