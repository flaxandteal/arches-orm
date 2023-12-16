## Note that some of this is based heavily on
## github.com/archesproject/arches
## and should be considered AGPLv3.

import logging

logger = logging.getLogger(__name__)


def add_hooks() -> set[str]:
    from .hooks import HOOKS

    return HOOKS
