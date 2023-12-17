# Module arches_orm.view_models.user

??? example "View Source"
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

## Classes

### UserProtocol

```python3
class UserProtocol(
    *args,
    **kwargs
)
```

Provides a standard format for exposing a user.

??? example "View Source"
        class UserProtocol(Protocol):

            """Provides a standard format for exposing a user."""

            pk: int

            email: str

------

#### Ancestors (in MRO)

* typing.Protocol
* typing.Generic

### UserViewModelMixin

```python3
class UserViewModelMixin(
    /,
    *args,
    **kwargs
)
```

Wraps a user, so that a Django User can be obtained.

To access the actual user, use `.user`.

??? example "View Source"
        class UserViewModelMixin(ViewModel):

            """Wraps a user, so that a Django User can be obtained.

            To access the actual user, use `.user`.

            """

            ...

------

#### Ancestors (in MRO)

* arches_orm.view_models._base.ViewModel

#### Descendants

* arches_orm.arches_django.datatypes.user.UserViewModel