## Note that some of this is based heavily on
## github.com/archesproject/arches
## and should be considered AGPLv3.

import logging

from ._internals.wrapper import ResourceModelWrapper
from ._internals.wkrm import resource_models
from ._internals.utils import (
    get_well_known_resource_model_by_class_name,
    get_well_known_resource_model_by_graph_id,
    attempt_well_known_resource_model,
)
from . import models

logger = logging.getLogger(__name__)

models.__dict__.update(resource_models)


def add_hooks() -> set[str]:
    from ._internals.hooks import HOOKS

    return HOOKS


__all__ = [
    "ResourceModelWrapper",
    "models",
    "get_well_known_resource_model_by_class_name",
    "get_well_known_resource_model_by_graph_id",
    "attempt_well_known_resource_model",
]
