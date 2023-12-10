import logging
from django.conf import settings
from typing import Callable
from .wrapper import ResourceModelWrapper


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

def _make_wkrm(wkrm_definition):
    try:
        return type(
            wkrm_definition.model_class_name,
            (ResourceModelWrapper,),
            {},
            well_known_resource_model=wkrm_definition,
        )
    except KeyError as e:
        logger.error("A WKRM, or its declared nodes, are missing: %s", wkrm_definition.model_class_name)
        logger.exception(e)

resource_models = {
    wkrm.model_class_name: _make_wkrm(wkrm)
    for wkrm in WELL_KNOWN_RESOURCE_MODELS
}
resource_models_by_graph_id = {rm.graphid: rm for rm in resource_models.values() if rm}
