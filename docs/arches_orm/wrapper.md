# Module arches_orm.wrapper

??? example "View Source"
        import logging

        import uuid

        from abc import (abstractmethod, abstractclassmethod, abstractstaticmethod)

        from .view_models import WKRI as Resource

        logger = logging.getLogger(__name__)

        class AdapterManager:

            default_adapter = None

            def __init__(self):

                self.adapters = {}

            def register_adapter(self, wrapper_cls):

                key = str(wrapper_cls)

                if key in self.adapters:

                    raise RuntimeError(

                        "Cannot register same adapter multiple times"

                    )

                if len(self.adapters) and not self.default_adapter:

                    raise RuntimeError(

                        "Must set a default adapter, if registering multiple in one process"

                    )

                self.adapters[key] = wrapper_cls

            def set_default_adapter(self, default_adapter):

                self.default_adapter = default_adapter

            def get_adapter(self, key=None):

                if not self.adapters:

                    raise RuntimeError(

                        "Must have at least one adapter available, "

                        "did you mean to import an adapter module?"

                    )

                if key is not None:

                    adapter = self.adapters[key]

                elif len(self.adapters) > 1:

                    if not self.default_adapter:

                        raise RuntimeError(

                            "You have imported multiple adapters, "

                            "you must set an explicit default."

                        )

                    adapter = self.adapters[self.default_adapter]

                else:

                    adapter = list(self.adapters.values())[0]

                return adapter

        ADAPTER_MANAGER = AdapterManager()

        get_adapter = ADAPTER_MANAGER.get_adapter

        class ResourceWrapper(Resource):

            """Superclass of all well-known resources.

            When you use, `Person`, etc. it will be this class in disguise.

            """

            model_name: str

            graphid: str

            id: str

            _values: dict = None

            _cross_record: dict = None

            _pending_relationships: list = None

            _related_prefetch: list = None

            resource: Resource

            def __getitem__(self, key):

                return self.__getattr__(key)

            def __setitem__(self, key, value):

                return self.__setattr__(key, value)

            def __eq__(self, other):

                return (

                    self.id and other.id and

                    self.id == other.id and

                    self.__class__ == other.__class__

                )

            def __setattr__(self, key, value):

                """Set Python values for nodes attributes."""

                if key in (

                    "id",

                    "_new_id",

                    "_values",

                    "resource",

                    "_root_node",

                    "_cross_record",

                    "_related_prefetch",

                    "_pending_relationships",

                ):

                    super().__setattr__(key, value)

                else:

                    setattr(self.get_root().value, key, value)

            def __getattr__(self, key):

                """Retrieve Python values for nodes attributes."""

                return getattr(self.get_root().value, key)

            def __init__(

                self,

                id=None,

                _new_id=None,

                resource=None,

                cross_record=None,

                related_prefetch=None,

                **kwargs,

            ):

                """Build well-known resource.

                Not normally called manually, this is the underlying constructor for

                well-known resources.

                """

                self._values = {}

                self.id = id if isinstance(id, uuid.UUID) else uuid.UUID(id) if id else None

                self._new_id = _new_id if isinstance(_new_id, uuid.UUID) else uuid.UUID(_new_id) if _new_id else None

                self.resource = resource

                self._cross_record = cross_record

                self._related_prefetch = related_prefetch

                for key, value in kwargs.items():

                    setattr(self, key, value)

            @classmethod

            def create_bulk(cls, fields: list, do_index: bool = True):

                raise NotImplementedError("The bulk_create module needs to be rewritten")

            @classmethod

            def create(cls, _no_save=False, _do_index=True, **kwargs):

                """Create a new well-known resource and Arches resource from field values."""

                # If an ID is supplied, it should be treated as desired, not existing.

                if "id" in kwargs:

                    kwargs["_new_id"] = kwargs["id"]

                    del kwargs["id"]

                inst = cls.build(**kwargs)

                if not _no_save:

                    inst.save()

                return inst

            @classmethod

            def build(cls, **kwargs):

                """Create a new well-known resource.

                Makes a well-known resource but not (yet) Arches resource,

                from field values.

                """

                values = {}

                for key, arg in kwargs.items():

                    if "." not in key:

                        values[key] = arg

                inst = cls(**values)

                for key, val in kwargs.items():

                    if "." in key:

                        level = inst

                        for token in key.split(".")[:-1]:

                            level = getattr(level, token)

                        setattr(level, key.split(".")[-1], val)

                return inst

            def update(self, values: dict):

                """Apply a dictionary of updates to fields."""

                for key, val in values.items():

                    setattr(self, key, val)

            def save(self):

                """Rebuild and save the underlying resource."""

                resource = self.to_resource(strict=True)

                resource.save()

                self.id = resource.pk

                return self

            def describe(self):

                """Give a textual description of this well-known resource."""

                from tabulate import tabulate

                description = (

                    f"{self.__class__.__name__}: {str(self)} <ri:{self.id} g:{self.graphid}>\n"

                )

                table = [["PROPERTY", "TYPE", "VALUE"]]

                for key, value in self._values.items():

                    if isinstance(value, list):

                        if value:

                            table.append([key, value[0].__class__.__name__, str(value[0])])

                            for val in value[1:]:

                                table.append(["", val.__class__.__name__, str(val)])

                        else:

                            table.append([key, "", "(empty)"])

                    else:

                        table.append([key, value.value.__class__.__name__, str(value)])

                return description + tabulate(table)

            def __str__(self):

                """Convert to string."""

                return str(self._wkrm.to_string(self))

            def __init_subclass__(cls, well_known_resource_model=None, adapter=False):

                """Create a new well-known resource model wrapper, from an WKRM."""

                if adapter:

                    ADAPTER_MANAGER.register_adapter(cls.get_adapter())

                else:

                    if not well_known_resource_model:

                        raise RuntimeError("Must try to wrap a real model")

                    cls._model_name = well_known_resource_model.model_name

                    cls.graphid = well_known_resource_model.graphid

                    cls._wkrm = well_known_resource_model

                    cls._add_events()

            @abstractclassmethod

            def search(cls, text, fields=None, _total=None):

                """Search for resources of this model, and return as well-known resources."""

            @abstractclassmethod

            def all_ids(cls):

                """Get IDs for all resources of this type."""

            @abstractclassmethod

            def all(cls, related_prefetch=None):

                """Get all resources of this type."""

            @abstractclassmethod

            def find(cls, resourceinstanceid):

                """Find an individual well-known resource by instance ID."""

            @abstractmethod

            def delete(self):

                """Delete the underlying resource."""

            @abstractmethod

            def remove(self):

                """When called via a relationship (dot), remove the relationship."""

            @abstractmethod

            def append(self, _no_save=False):

                """When called via a relationship (dot), append to the relationship."""

            @abstractclassmethod

            def values_from_resource(

                cls, nodes, node_objs, resource, related_prefetch=None, wkri=None

            ):

                """Populate fields from the ID-referenced Arches resource."""

            @abstractclassmethod

            def where(cls, cross_record=None, **kwargs):

                """Do a filtered query returning a list of well-known resources."""

            @abstractstaticmethod

            def get_adapter():

                """Get the adapter that encapsulates this wrapper."""

## Variables

```python3
ADAPTER_MANAGER
```

```python3
logger
```

## Functions

    
### get_adapter

```python3
def get_adapter(
    key=None
)
```

??? example "View Source"
            def get_adapter(self, key=None):

                if not self.adapters:

                    raise RuntimeError(

                        "Must have at least one adapter available, "

                        "did you mean to import an adapter module?"

                    )

                if key is not None:

                    adapter = self.adapters[key]

                elif len(self.adapters) > 1:

                    if not self.default_adapter:

                        raise RuntimeError(

                            "You have imported multiple adapters, "

                            "you must set an explicit default."

                        )

                    adapter = self.adapters[self.default_adapter]

                else:

                    adapter = list(self.adapters.values())[0]

                return adapter

## Classes

### AdapterManager

```python3
class AdapterManager(
    
)
```

??? example "View Source"
        class AdapterManager:

            default_adapter = None

            def __init__(self):

                self.adapters = {}

            def register_adapter(self, wrapper_cls):

                key = str(wrapper_cls)

                if key in self.adapters:

                    raise RuntimeError(

                        "Cannot register same adapter multiple times"

                    )

                if len(self.adapters) and not self.default_adapter:

                    raise RuntimeError(

                        "Must set a default adapter, if registering multiple in one process"

                    )

                self.adapters[key] = wrapper_cls

            def set_default_adapter(self, default_adapter):

                self.default_adapter = default_adapter

            def get_adapter(self, key=None):

                if not self.adapters:

                    raise RuntimeError(

                        "Must have at least one adapter available, "

                        "did you mean to import an adapter module?"

                    )

                if key is not None:

                    adapter = self.adapters[key]

                elif len(self.adapters) > 1:

                    if not self.default_adapter:

                        raise RuntimeError(

                            "You have imported multiple adapters, "

                            "you must set an explicit default."

                        )

                    adapter = self.adapters[self.default_adapter]

                else:

                    adapter = list(self.adapters.values())[0]

                return adapter

------

#### Class variables

```python3
default_adapter
```

#### Methods

    
#### get_adapter

```python3
def get_adapter(
    self,
    key=None
)
```

??? example "View Source"
            def get_adapter(self, key=None):

                if not self.adapters:

                    raise RuntimeError(

                        "Must have at least one adapter available, "

                        "did you mean to import an adapter module?"

                    )

                if key is not None:

                    adapter = self.adapters[key]

                elif len(self.adapters) > 1:

                    if not self.default_adapter:

                        raise RuntimeError(

                            "You have imported multiple adapters, "

                            "you must set an explicit default."

                        )

                    adapter = self.adapters[self.default_adapter]

                else:

                    adapter = list(self.adapters.values())[0]

                return adapter

    
#### register_adapter

```python3
def register_adapter(
    self,
    wrapper_cls
)
```

??? example "View Source"
            def register_adapter(self, wrapper_cls):

                key = str(wrapper_cls)

                if key in self.adapters:

                    raise RuntimeError(

                        "Cannot register same adapter multiple times"

                    )

                if len(self.adapters) and not self.default_adapter:

                    raise RuntimeError(

                        "Must set a default adapter, if registering multiple in one process"

                    )

                self.adapters[key] = wrapper_cls

    
#### set_default_adapter

```python3
def set_default_adapter(
    self,
    default_adapter
)
```

??? example "View Source"
            def set_default_adapter(self, default_adapter):

                self.default_adapter = default_adapter

### ResourceWrapper

```python3
class ResourceWrapper(
    id=None,
    _new_id=None,
    resource=None,
    cross_record=None,
    related_prefetch=None,
    **kwargs
)
```

Superclass of all well-known resources.

When you use, `Person`, etc. it will be this class in disguise.

??? example "View Source"
        class ResourceWrapper(Resource):

            """Superclass of all well-known resources.

            When you use, `Person`, etc. it will be this class in disguise.

            """

            model_name: str

            graphid: str

            id: str

            _values: dict = None

            _cross_record: dict = None

            _pending_relationships: list = None

            _related_prefetch: list = None

            resource: Resource

            def __getitem__(self, key):

                return self.__getattr__(key)

            def __setitem__(self, key, value):

                return self.__setattr__(key, value)

            def __eq__(self, other):

                return (

                    self.id and other.id and

                    self.id == other.id and

                    self.__class__ == other.__class__

                )

            def __setattr__(self, key, value):

                """Set Python values for nodes attributes."""

                if key in (

                    "id",

                    "_new_id",

                    "_values",

                    "resource",

                    "_root_node",

                    "_cross_record",

                    "_related_prefetch",

                    "_pending_relationships",

                ):

                    super().__setattr__(key, value)

                else:

                    setattr(self.get_root().value, key, value)

            def __getattr__(self, key):

                """Retrieve Python values for nodes attributes."""

                return getattr(self.get_root().value, key)

            def __init__(

                self,

                id=None,

                _new_id=None,

                resource=None,

                cross_record=None,

                related_prefetch=None,

                **kwargs,

            ):

                """Build well-known resource.

                Not normally called manually, this is the underlying constructor for

                well-known resources.

                """

                self._values = {}

                self.id = id if isinstance(id, uuid.UUID) else uuid.UUID(id) if id else None

                self._new_id = _new_id if isinstance(_new_id, uuid.UUID) else uuid.UUID(_new_id) if _new_id else None

                self.resource = resource

                self._cross_record = cross_record

                self._related_prefetch = related_prefetch

                for key, value in kwargs.items():

                    setattr(self, key, value)

            @classmethod

            def create_bulk(cls, fields: list, do_index: bool = True):

                raise NotImplementedError("The bulk_create module needs to be rewritten")

            @classmethod

            def create(cls, _no_save=False, _do_index=True, **kwargs):

                """Create a new well-known resource and Arches resource from field values."""

                # If an ID is supplied, it should be treated as desired, not existing.

                if "id" in kwargs:

                    kwargs["_new_id"] = kwargs["id"]

                    del kwargs["id"]

                inst = cls.build(**kwargs)

                if not _no_save:

                    inst.save()

                return inst

            @classmethod

            def build(cls, **kwargs):

                """Create a new well-known resource.

                Makes a well-known resource but not (yet) Arches resource,

                from field values.

                """

                values = {}

                for key, arg in kwargs.items():

                    if "." not in key:

                        values[key] = arg

                inst = cls(**values)

                for key, val in kwargs.items():

                    if "." in key:

                        level = inst

                        for token in key.split(".")[:-1]:

                            level = getattr(level, token)

                        setattr(level, key.split(".")[-1], val)

                return inst

            def update(self, values: dict):

                """Apply a dictionary of updates to fields."""

                for key, val in values.items():

                    setattr(self, key, val)

            def save(self):

                """Rebuild and save the underlying resource."""

                resource = self.to_resource(strict=True)

                resource.save()

                self.id = resource.pk

                return self

            def describe(self):

                """Give a textual description of this well-known resource."""

                from tabulate import tabulate

                description = (

                    f"{self.__class__.__name__}: {str(self)} <ri:{self.id} g:{self.graphid}>\n"

                )

                table = [["PROPERTY", "TYPE", "VALUE"]]

                for key, value in self._values.items():

                    if isinstance(value, list):

                        if value:

                            table.append([key, value[0].__class__.__name__, str(value[0])])

                            for val in value[1:]:

                                table.append(["", val.__class__.__name__, str(val)])

                        else:

                            table.append([key, "", "(empty)"])

                    else:

                        table.append([key, value.value.__class__.__name__, str(value)])

                return description + tabulate(table)

            def __str__(self):

                """Convert to string."""

                return str(self._wkrm.to_string(self))

            def __init_subclass__(cls, well_known_resource_model=None, adapter=False):

                """Create a new well-known resource model wrapper, from an WKRM."""

                if adapter:

                    ADAPTER_MANAGER.register_adapter(cls.get_adapter())

                else:

                    if not well_known_resource_model:

                        raise RuntimeError("Must try to wrap a real model")

                    cls._model_name = well_known_resource_model.model_name

                    cls.graphid = well_known_resource_model.graphid

                    cls._wkrm = well_known_resource_model

                    cls._add_events()

            @abstractclassmethod

            def search(cls, text, fields=None, _total=None):

                """Search for resources of this model, and return as well-known resources."""

            @abstractclassmethod

            def all_ids(cls):

                """Get IDs for all resources of this type."""

            @abstractclassmethod

            def all(cls, related_prefetch=None):

                """Get all resources of this type."""

            @abstractclassmethod

            def find(cls, resourceinstanceid):

                """Find an individual well-known resource by instance ID."""

            @abstractmethod

            def delete(self):

                """Delete the underlying resource."""

            @abstractmethod

            def remove(self):

                """When called via a relationship (dot), remove the relationship."""

            @abstractmethod

            def append(self, _no_save=False):

                """When called via a relationship (dot), append to the relationship."""

            @abstractclassmethod

            def values_from_resource(

                cls, nodes, node_objs, resource, related_prefetch=None, wkri=None

            ):

                """Populate fields from the ID-referenced Arches resource."""

            @abstractclassmethod

            def where(cls, cross_record=None, **kwargs):

                """Do a filtered query returning a list of well-known resources."""

            @abstractstaticmethod

            def get_adapter():

                """Get the adapter that encapsulates this wrapper."""

------

#### Ancestors (in MRO)

* arches_orm.view_models.WKRI

#### Descendants

* arches_orm.arches_django.wrapper.ArchesDjangoResourceWrapper

#### Static methods

    
#### all

```python3
def all(
    related_prefetch=None
)
```

Get all resources of this type.

??? example "View Source"
            @abstractclassmethod

            def all(cls, related_prefetch=None):

                """Get all resources of this type."""

    
#### all_ids

```python3
def all_ids(
    
)
```

Get IDs for all resources of this type.

??? example "View Source"
            @abstractclassmethod

            def all_ids(cls):

                """Get IDs for all resources of this type."""

    
#### build

```python3
def build(
    **kwargs
)
```

Create a new well-known resource.

Makes a well-known resource but not (yet) Arches resource,
from field values.

??? example "View Source"
            @classmethod

            def build(cls, **kwargs):

                """Create a new well-known resource.

                Makes a well-known resource but not (yet) Arches resource,

                from field values.

                """

                values = {}

                for key, arg in kwargs.items():

                    if "." not in key:

                        values[key] = arg

                inst = cls(**values)

                for key, val in kwargs.items():

                    if "." in key:

                        level = inst

                        for token in key.split(".")[:-1]:

                            level = getattr(level, token)

                        setattr(level, key.split(".")[-1], val)

                return inst

    
#### create

```python3
def create(
    _no_save=False,
    _do_index=True,
    **kwargs
)
```

Create a new well-known resource and Arches resource from field values.

??? example "View Source"
            @classmethod

            def create(cls, _no_save=False, _do_index=True, **kwargs):

                """Create a new well-known resource and Arches resource from field values."""

                # If an ID is supplied, it should be treated as desired, not existing.

                if "id" in kwargs:

                    kwargs["_new_id"] = kwargs["id"]

                    del kwargs["id"]

                inst = cls.build(**kwargs)

                if not _no_save:

                    inst.save()

                return inst

    
#### create_bulk

```python3
def create_bulk(
    fields: list,
    do_index: bool = True
)
```

??? example "View Source"
            @classmethod

            def create_bulk(cls, fields: list, do_index: bool = True):

                raise NotImplementedError("The bulk_create module needs to be rewritten")

    
#### find

```python3
def find(
    resourceinstanceid
)
```

Find an individual well-known resource by instance ID.

??? example "View Source"
            @abstractclassmethod

            def find(cls, resourceinstanceid):

                """Find an individual well-known resource by instance ID."""

    
#### get_adapter

```python3
def get_adapter(
    
)
```

Get the adapter that encapsulates this wrapper.

??? example "View Source"
            @abstractstaticmethod

            def get_adapter():

                """Get the adapter that encapsulates this wrapper."""

    
#### search

```python3
def search(
    text,
    fields=None,
    _total=None
)
```

Search for resources of this model, and return as well-known resources.

??? example "View Source"
            @abstractclassmethod

            def search(cls, text, fields=None, _total=None):

                """Search for resources of this model, and return as well-known resources."""

    
#### values_from_resource

```python3
def values_from_resource(
    nodes,
    node_objs,
    resource,
    related_prefetch=None,
    wkri=None
)
```

Populate fields from the ID-referenced Arches resource.

??? example "View Source"
            @abstractclassmethod

            def values_from_resource(

                cls, nodes, node_objs, resource, related_prefetch=None, wkri=None

            ):

                """Populate fields from the ID-referenced Arches resource."""

    
#### where

```python3
def where(
    cross_record=None,
    **kwargs
)
```

Do a filtered query returning a list of well-known resources.

??? example "View Source"
            @abstractclassmethod

            def where(cls, cross_record=None, **kwargs):

                """Do a filtered query returning a list of well-known resources."""

#### Methods

    
#### append

```python3
def append(
    self,
    _no_save=False
)
```

When called via a relationship (dot), append to the relationship.

??? example "View Source"
            @abstractmethod

            def append(self, _no_save=False):

                """When called via a relationship (dot), append to the relationship."""

    
#### delete

```python3
def delete(
    self
)
```

Delete the underlying resource.

??? example "View Source"
            @abstractmethod

            def delete(self):

                """Delete the underlying resource."""

    
#### describe

```python3
def describe(
    self
)
```

Give a textual description of this well-known resource.

??? example "View Source"
            def describe(self):

                """Give a textual description of this well-known resource."""

                from tabulate import tabulate

                description = (

                    f"{self.__class__.__name__}: {str(self)} <ri:{self.id} g:{self.graphid}>\n"

                )

                table = [["PROPERTY", "TYPE", "VALUE"]]

                for key, value in self._values.items():

                    if isinstance(value, list):

                        if value:

                            table.append([key, value[0].__class__.__name__, str(value[0])])

                            for val in value[1:]:

                                table.append(["", val.__class__.__name__, str(val)])

                        else:

                            table.append([key, "", "(empty)"])

                    else:

                        table.append([key, value.value.__class__.__name__, str(value)])

                return description + tabulate(table)

    
#### remove

```python3
def remove(
    self
)
```

When called via a relationship (dot), remove the relationship.

??? example "View Source"
            @abstractmethod

            def remove(self):

                """When called via a relationship (dot), remove the relationship."""

    
#### save

```python3
def save(
    self
)
```

Rebuild and save the underlying resource.

??? example "View Source"
            def save(self):

                """Rebuild and save the underlying resource."""

                resource = self.to_resource(strict=True)

                resource.save()

                self.id = resource.pk

                return self

    
#### update

```python3
def update(
    self,
    values: dict
)
```

Apply a dictionary of updates to fields.

??? example "View Source"
            def update(self, values: dict):

                """Apply a dictionary of updates to fields."""

                for key, val in values.items():

                    setattr(self, key, val)