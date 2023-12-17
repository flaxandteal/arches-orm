# Module arches_orm.arches_django.adapter

??? example "View Source"
        from arches.app.models.resource import Resource

        import logging

        logger = logging.getLogger(__name__)

        

        LOAD_FULL_NODE_OBJECTS = True

        LOAD_ALL_NODES = True

        class ArchesDjangoAdapter:

            def __str__(self):

                return "arches-django"

            def get_wrapper(self):

                from .wrapper import ArchesDjangoResourceWrapper

                return ArchesDjangoResourceWrapper

            def load_from_id(self, resource_id, from_prefetch=None):

                from arches_orm.utils import get_resource_models_for_adapter

                resource = (

                    from_prefetch(resource_id)

                    if from_prefetch is not None

                    else Resource.objects.get(pk=resource_id)

                )

                resource_models_by_graph_id = get_resource_models_for_adapter(str(self))["by-graph-id"]

                if str(resource.graph_id) not in resource_models_by_graph_id:

                    logger.error("Tried to load non-existent WKRM: %s", resource_id)

                    return None

                return resource_models_by_graph_id[str(resource.graph_id)].from_resource(

                    resource, related_prefetch=from_prefetch

                )

            def get_hooks(self):

                from .hooks import HOOKS

                return HOOKS

## Variables

```python3
LOAD_ALL_NODES
```

```python3
LOAD_FULL_NODE_OBJECTS
```

```python3
logger
```

## Classes

### ArchesDjangoAdapter

```python3
class ArchesDjangoAdapter(
    /,
    *args,
    **kwargs
)
```

??? example "View Source"
        class ArchesDjangoAdapter:

            def __str__(self):

                return "arches-django"

            def get_wrapper(self):

                from .wrapper import ArchesDjangoResourceWrapper

                return ArchesDjangoResourceWrapper

            def load_from_id(self, resource_id, from_prefetch=None):

                from arches_orm.utils import get_resource_models_for_adapter

                resource = (

                    from_prefetch(resource_id)

                    if from_prefetch is not None

                    else Resource.objects.get(pk=resource_id)

                )

                resource_models_by_graph_id = get_resource_models_for_adapter(str(self))["by-graph-id"]

                if str(resource.graph_id) not in resource_models_by_graph_id:

                    logger.error("Tried to load non-existent WKRM: %s", resource_id)

                    return None

                return resource_models_by_graph_id[str(resource.graph_id)].from_resource(

                    resource, related_prefetch=from_prefetch

                )

            def get_hooks(self):

                from .hooks import HOOKS

                return HOOKS

------

#### Methods

    
#### get_hooks

```python3
def get_hooks(
    self
)
```

??? example "View Source"
            def get_hooks(self):

                from .hooks import HOOKS

                return HOOKS

    
#### get_wrapper

```python3
def get_wrapper(
    self
)
```

??? example "View Source"
            def get_wrapper(self):

                from .wrapper import ArchesDjangoResourceWrapper

                return ArchesDjangoResourceWrapper

    
#### load_from_id

```python3
def load_from_id(
    self,
    resource_id,
    from_prefetch=None
)
```

??? example "View Source"
            def load_from_id(self, resource_id, from_prefetch=None):

                from arches_orm.utils import get_resource_models_for_adapter

                resource = (

                    from_prefetch(resource_id)

                    if from_prefetch is not None

                    else Resource.objects.get(pk=resource_id)

                )

                resource_models_by_graph_id = get_resource_models_for_adapter(str(self))["by-graph-id"]

                if str(resource.graph_id) not in resource_models_by_graph_id:

                    logger.error("Tried to load non-existent WKRM: %s", resource_id)

                    return None

                return resource_models_by_graph_id[str(resource.graph_id)].from_resource(

                    resource, related_prefetch=from_prefetch

                )