# Module arches_orm.arches_django.datatypes

??? example "View Source"
        from ._register import get_view_model_for_datatype

        from . import (

            concepts,

            semantic,

            resource_instances,

            string,

            user

        )

        __all__ = [

            "get_view_model_for_datatype"

        ]

## Sub-modules

* [arches_orm.arches_django.datatypes.concepts](concepts/)
* [arches_orm.arches_django.datatypes.resource_instances](resource_instances/)
* [arches_orm.arches_django.datatypes.semantic](semantic/)
* [arches_orm.arches_django.datatypes.string](string/)
* [arches_orm.arches_django.datatypes.user](user/)

## Functions

    
### get_view_model_for_datatype

```python3
def get_view_model_for_datatype(
    tile,
    node,
    parent,
    child_nodes,
    value=None
)
```

??? example "View Source"
        def get_view_model_for_datatype(tile, node, parent, child_nodes, value=None):

            return REGISTER.make(

                tile, node, value=value, parent=parent, child_nodes=child_nodes

            )