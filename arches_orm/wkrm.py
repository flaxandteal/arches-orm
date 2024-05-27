import logging
from typing import Callable
from .adapter import get_adapter
from .view_models.resources import ResourceInstanceViewModel


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
    remapping: dict | None
    total_remap: bool
    to_string: Callable

    @property
    def model_class_name(self):
        return self.model_name.replace(" ", "")

    def __init__(self, model_name, graphid, __str__=None, total_remap=False, remapping=None, **kwargs):
        self.model_name = model_name
        self.graphid = graphid
        self.to_string = __str__ or repr
        self.remapping = remapping
        self.total_remap = False
        self.nodes = kwargs


WELL_KNOWN_RESOURCE_MODELS = [
    WKRM(**model) for model in get_adapter().get_wkrm_definitions()
]


def _make_wkrm(wkrm_definition, adapter):
    try:
        orm_model = type(
            f"{wkrm_definition.model_class_name}Wrapper",
            (adapter.get_wrapper(),),
            {"proxy": False, "view_model": None},
            well_known_resource_model=wkrm_definition,
            context=adapter.get_context(),
        )
        orm_view_model = type(
            wkrm_definition.model_class_name,
            (ResourceInstanceViewModel,),
            {"_": orm_model}
        )
        orm_model.view_model = orm_view_model
        return orm_view_model
    except KeyError as e:
        logger.error(
            "A WKRM, or its declared nodes, are missing: %s",
            wkrm_definition.model_class_name,
        )
        logger.exception(e)


resource_models = {}


def get_resource_models_for_adapter(adapter_name: str | None = None):
    adapter = get_adapter(adapter_name)
    if str(adapter) not in resource_models:
        resource_models[str(adapter)] = {}
        resource_models[str(adapter)]["by-class"] = {}
        for wkrm in WELL_KNOWN_RESOURCE_MODELS:
            try:
                resource_models[str(adapter)]["by-class"][wkrm.model_class_name] = _make_wkrm(wkrm, adapter)
            except Exception as exc:
                logger.error("Could not load well-known resource model %s for adapter %s", str(wkrm.model_class_name), str(adapter))
                logger.exception(exc)
                logger.error("...continuing, to prevent circularity.")
        resource_models[str(adapter)]["by-graph-id"] = {
            rm.graphid: rm
            for rm in resource_models[str(adapter)]["by-class"].values()
            if rm
        }
    return resource_models[str(adapter)]


def get_well_known_resource_model_by_class_name(
    class_name, default=None, adapter: str | None = None
):
    """Turns a class-name as a string into a well-known resource model wrapper."""
    resource_models = get_resource_models_for_adapter(adapter)["by-class"]
    return resource_models.get(class_name, default)


def get_well_known_resource_model_by_graph_id(
    graphid, default=None, adapter: str | None = None
):
    """Turns a graph into a well-known resource model wrapper, by ID, if known."""
    resource_models_by_graph_id = get_resource_models_for_adapter(adapter)[
        "by-graph-id"
    ]
    return resource_models_by_graph_id.get(str(graphid), default)


def attempt_well_known_resource_model(
    resource_id, from_prefetch=None, adapter=None, lazy=False, **kwargs
):
    """Attempts to find and create a well-known resource from a resource ID

    This is the simplest entry-point if you do not know the model of the resource
    you have. Bear in mind, it will return None if a well-known resource model
    is not matched.
    """

    return get_adapter(adapter).load_from_id(
        resource_id=resource_id, from_prefetch=from_prefetch, lazy=lazy
    )

get_resource_models_for_adapter()
