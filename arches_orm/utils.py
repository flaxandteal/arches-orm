import logging
from .adapter import get_adapter
from .wkrm import get_resource_models_for_adapter

logger = logging.getLogger(__name__)


def get_well_known_resource_model_by_class_name(class_name, default=None, adapter: str | None=None):
    """Turns a class-name as a string into a well-known resource model wrapper."""
    resource_models = get_resource_models_for_adapter(adapter)["by-class"]
    return resource_models.get(class_name, default)


def get_well_known_resource_model_by_graph_id(graphid, default=None, adapter: str | None=None):
    """Turns a graph into a well-known resource model wrapper, by ID, if known."""
    resource_models_by_graph_id = get_resource_models_for_adapter(adapter)["by-graph-id"]
    return resource_models_by_graph_id.get(str(graphid), default)


def attempt_well_known_resource_model(resource_id, from_prefetch=None, adapter=None, **kwargs):
    """Attempts to find and create a well-known resource from a resource ID

    This is the simplest entry-point if you do not know the model of the resource
    you have. Bear in mind, it will return None if a well-known resource model
    is not matched.
    """

    return get_adapter(adapter).load_from_id(
        resource_id=resource_id,
        from_prefetch=from_prefetch
    )
