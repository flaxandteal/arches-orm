# Module arches_orm.view_models.resources

??? example "View Source"
        from typing import Protocol

        import uuid

        from collections import UserList

        from ._base import (

            ViewModel,

        )

        class ResourceProtocol(Protocol):

            graphid: uuid.UUID

            _cross_record: dict | None = None

        

        class RelatedResourceInstanceViewModelMixin(ViewModel):

            """Wraps a resource instance.

            Subclasses str, so it can be handled like a string enum, but keeps

            the `.value`, `.lang` and `.text` properties cached, so you can

            find out more.

            """

            def get_relationships(self):

                # TODO: nesting

                return [self]

        

        class RelatedResourceInstanceListViewModel(UserList, ViewModel):

            """Wraps a concept list, allowing interrogation.

            Subclasses list, so its members can be handled like a string enum, but keeps

            the `.value`, `.lang` and `.text` properties cached, so you can

            find out more.

            """

            def __init__(

                self,

                parent_wkri,

                resource_instance_list,

                make_ri_cb,

            ):

                self._parent_wkri = parent_wkri

                self._make_ri_cb = make_ri_cb

                for resource_instance in resource_instance_list:

                    self.append(resource_instance)

            def append(self, item: str | uuid.UUID | ResourceProtocol):

                """Add a well-known resource to the list."""

                if isinstance(item, RelatedResourceInstanceViewModelMixin):

                    raise NotImplementedError("Cannot currently reparent related resources")

                resource_instance = item if isinstance(item, ResourceProtocol) else None

                resource_instance_id = item if isinstance(item, str | uuid.UUID) else None

                value = self._make_ri_cb(resource_instance or resource_instance_id)

                if str(value._cross_record["wkriFrom"]) != str(self._parent_wkri.id):

                    raise NotImplementedError("Cannot current reparent related resources")

                return super().append(item)

            def remove(self, value):

                for item in self:

                    if value.resourceinstanceid == item.resourceinstanceid:

                        value = item

                super().remove(value)

            def get_relationships(self):

                return sum((x.get_relationships() for x in self), [])

## Classes

### RelatedResourceInstanceListViewModel

```python3
class RelatedResourceInstanceListViewModel(
    parent_wkri,
    resource_instance_list,
    make_ri_cb
)
```

Wraps a concept list, allowing interrogation.

Subclasses list, so its members can be handled like a string enum, but keeps
the `.value`, `.lang` and `.text` properties cached, so you can
find out more.

??? example "View Source"
        class RelatedResourceInstanceListViewModel(UserList, ViewModel):

            """Wraps a concept list, allowing interrogation.

            Subclasses list, so its members can be handled like a string enum, but keeps

            the `.value`, `.lang` and `.text` properties cached, so you can

            find out more.

            """

            def __init__(

                self,

                parent_wkri,

                resource_instance_list,

                make_ri_cb,

            ):

                self._parent_wkri = parent_wkri

                self._make_ri_cb = make_ri_cb

                for resource_instance in resource_instance_list:

                    self.append(resource_instance)

            def append(self, item: str | uuid.UUID | ResourceProtocol):

                """Add a well-known resource to the list."""

                if isinstance(item, RelatedResourceInstanceViewModelMixin):

                    raise NotImplementedError("Cannot currently reparent related resources")

                resource_instance = item if isinstance(item, ResourceProtocol) else None

                resource_instance_id = item if isinstance(item, str | uuid.UUID) else None

                value = self._make_ri_cb(resource_instance or resource_instance_id)

                if str(value._cross_record["wkriFrom"]) != str(self._parent_wkri.id):

                    raise NotImplementedError("Cannot current reparent related resources")

                return super().append(item)

            def remove(self, value):

                for item in self:

                    if value.resourceinstanceid == item.resourceinstanceid:

                        value = item

                super().remove(value)

            def get_relationships(self):

                return sum((x.get_relationships() for x in self), [])

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

#### Methods

    
#### append

```python3
def append(
    self,
    item: str | uuid.UUID | arches_orm.view_models.resources.ResourceProtocol
)
```

Add a well-known resource to the list.

??? example "View Source"
            def append(self, item: str | uuid.UUID | ResourceProtocol):

                """Add a well-known resource to the list."""

                if isinstance(item, RelatedResourceInstanceViewModelMixin):

                    raise NotImplementedError("Cannot currently reparent related resources")

                resource_instance = item if isinstance(item, ResourceProtocol) else None

                resource_instance_id = item if isinstance(item, str | uuid.UUID) else None

                value = self._make_ri_cb(resource_instance or resource_instance_id)

                if str(value._cross_record["wkriFrom"]) != str(self._parent_wkri.id):

                    raise NotImplementedError("Cannot current reparent related resources")

                return super().append(item)

    
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

    
#### get_relationships

```python3
def get_relationships(
    self
)
```

??? example "View Source"
            def get_relationships(self):

                return sum((x.get_relationships() for x in self), [])

    
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
    value
)
```

S.remove(value) -- remove first occurrence of value.

Raise ValueError if the value is not present.

??? example "View Source"
            def remove(self, value):

                for item in self:

                    if value.resourceinstanceid == item.resourceinstanceid:

                        value = item

                super().remove(value)

    
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

### RelatedResourceInstanceViewModelMixin

```python3
class RelatedResourceInstanceViewModelMixin(
    /,
    *args,
    **kwargs
)
```

Wraps a resource instance.

Subclasses str, so it can be handled like a string enum, but keeps
the `.value`, `.lang` and `.text` properties cached, so you can
find out more.

??? example "View Source"
        class RelatedResourceInstanceViewModelMixin(ViewModel):

            """Wraps a resource instance.

            Subclasses str, so it can be handled like a string enum, but keeps

            the `.value`, `.lang` and `.text` properties cached, so you can

            find out more.

            """

            def get_relationships(self):

                # TODO: nesting

                return [self]

------

#### Ancestors (in MRO)

* arches_orm.view_models._base.ViewModel

#### Methods

    
#### get_relationships

```python3
def get_relationships(
    self
)
```

??? example "View Source"
            def get_relationships(self):

                # TODO: nesting

                return [self]

### ResourceProtocol

```python3
class ResourceProtocol(
    *args,
    **kwargs
)
```

Base class for protocol classes.

Protocol classes are defined as::

    class Proto(Protocol):
        def meth(self) -> int:
            ...

Such classes are primarily used with static type checkers that recognize
structural subtyping (static duck-typing), for example::

    class C:
        def meth(self) -> int:
            return 0

    def func(x: Proto) -> int:
        return x.meth()

    func(C())  # Passes static type check

See PEP 544 for details. Protocol classes decorated with

??? example "View Source"
        class ResourceProtocol(Protocol):

            graphid: uuid.UUID

            _cross_record: dict | None = None

------

#### Ancestors (in MRO)

* typing.Protocol
* typing.Generic