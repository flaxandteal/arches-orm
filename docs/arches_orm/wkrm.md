# Module arches_orm.wkrm

??? example "View Source"
        import logging

        from django.conf import settings

        from typing import Callable

        from .adapter import get_adapter

        

        logger = logging.getLogger(__name__)

        

        class WKRM:

            """Well-known resource model definition.

            This provides the settings for a well-known resource model wrapper,

            in particular, the model's name, its graph ID, any node-specific settings

            and, if desired, a callback to render the resource to a string.

            """

            model_name: str

            graphid: str

            nodes: dict

            to_string: Callable

            @property

            def model_class_name(self):

                return self.model_name.replace(" ", "")

            def __init__(self, model_name, graphid, __str__=None, **kwargs):

                self.model_name = model_name

                self.graphid = graphid

                self.to_string = __str__ or repr

                self.nodes = kwargs

        

        WELL_KNOWN_RESOURCE_MODELS = [

            WKRM(**model) for model in settings.WELL_KNOWN_RESOURCE_MODELS

        ]

        

        def _make_wkrm(wkrm_definition, adapter):

            try:

                return type(

                    wkrm_definition.model_class_name,

                    (adapter.get_wrapper(),),

                    {},

                    well_known_resource_model=wkrm_definition,

                )

            except KeyError as e:

                logger.error(

                    "A WKRM, or its declared nodes, are missing: %s",

                    wkrm_definition.model_class_name,

                )

                logger.exception(e)

        

        resource_models = {}

        def get_resource_models_for_adapter(adapter_name: str | None=None):

            adapter = get_adapter(adapter_name)

            if str(adapter) not in resource_models:

                resource_models[str(adapter)] = {}

                resource_models[str(adapter)]["by-class"] = {

                    wkrm.model_class_name: _make_wkrm(wkrm, adapter) for wkrm in WELL_KNOWN_RESOURCE_MODELS

                }

                resource_models[str(adapter)]["by-graph-id"] = {

                    rm.graphid: rm for rm in resource_models[str(adapter)]["by-class"].values() if rm

                }

            return resource_models[str(adapter)]

        get_resource_models_for_adapter()

## Variables

```python3
WELL_KNOWN_RESOURCE_MODELS
```

```python3
logger
```

```python3
resource_models
```

## Functions

    
### get_resource_models_for_adapter

```python3
def get_resource_models_for_adapter(
    adapter_name: str | None = None
)
```

??? example "View Source"
        def get_resource_models_for_adapter(adapter_name: str | None=None):

            adapter = get_adapter(adapter_name)

            if str(adapter) not in resource_models:

                resource_models[str(adapter)] = {}

                resource_models[str(adapter)]["by-class"] = {

                    wkrm.model_class_name: _make_wkrm(wkrm, adapter) for wkrm in WELL_KNOWN_RESOURCE_MODELS

                }

                resource_models[str(adapter)]["by-graph-id"] = {

                    rm.graphid: rm for rm in resource_models[str(adapter)]["by-class"].values() if rm

                }

            return resource_models[str(adapter)]

## Classes

### WKRM

```python3
class WKRM(
    model_name,
    graphid,
    __str__=None,
    **kwargs
)
```

Well-known resource model definition.

This provides the settings for a well-known resource model wrapper,
in particular, the model's name, its graph ID, any node-specific settings
and, if desired, a callback to render the resource to a string.

??? example "View Source"
        class WKRM:

            """Well-known resource model definition.

            This provides the settings for a well-known resource model wrapper,

            in particular, the model's name, its graph ID, any node-specific settings

            and, if desired, a callback to render the resource to a string.

            """

            model_name: str

            graphid: str

            nodes: dict

            to_string: Callable

            @property

            def model_class_name(self):

                return self.model_name.replace(" ", "")

            def __init__(self, model_name, graphid, __str__=None, **kwargs):

                self.model_name = model_name

                self.graphid = graphid

                self.to_string = __str__ or repr

                self.nodes = kwargs

------

#### Instance variables

```python3
model_class_name
```