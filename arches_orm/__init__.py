## Note that some of this is based heavily on
## github.com/archesproject/arches
## and should be considered AGPLv3.

import logging

from ._internals.wrapper import ResourceModelWrapper
from ._internals.wkrm import resource_models
from ._internals.utils import *

logger = logging.getLogger(__name__)

globals().update(resource_models)


def add_hooks():
    from ._internals.hooks import check_resource_instance as _
