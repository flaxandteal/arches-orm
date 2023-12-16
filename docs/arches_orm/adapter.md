# Module arches_orm.adapter

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

        ADAPTER_MANAGER = AdapterManager()

        get_adapter = ADAPTER_MANAGER.get_adapter

## Variables

```python3
ADAPTER_MANAGER
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