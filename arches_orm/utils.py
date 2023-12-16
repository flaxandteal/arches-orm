from arches.app.models.resource import Resource
import logging
from .wkrm import resource_models, resource_models_by_graph_id
from .wrapper import ResourceModelWrapper

logger = logging.getLogger(__name__)


def get_well_known_resource_model_by_class_name(class_name, default=None):
    """Turns a class-name as a string into a well-known resource model wrapper."""
    return resource_models.get(class_name, default)


def get_well_known_resource_model_by_graph_id(graphid, default=None):
    """Turns a graph into a well-known resource model wrapper, by ID, if known."""
    return resource_models_by_graph_id.get(str(graphid), default)


def attempt_well_known_resource_model(resource_id, from_prefetch=None, **kwargs):
    """Attempts to find and create a well-known resource from a resource ID

    This is the simplest entry-point if you do not know the model of the resource
    you have. Bear in mind, it will return None if a well-known resource model
    is not matched.
    """

    resource = (
        from_prefetch(resource_id)
        if from_prefetch is not None
        else Resource.objects.get(pk=resource_id)
    )
    if resource is None:
        logger.error("Tried to load non-existent WKRM: %s", resource_id)
        return None
    if isinstance(resource, ResourceModelWrapper):
        return resource
    wkrm = get_well_known_resource_model_by_graph_id(resource.graph_id, default=None)
    if wkrm:
        return wkrm.from_resource(resource, **kwargs)
    return None
