import logging
from arches_orm.adapter import Adapter
from .wrapper import _DUMMY_STORE

logger = logging.getLogger(__name__)


LOAD_FULL_NODE_OBJECTS = True
LOAD_ALL_NODES = True

WKRM_DEFINITIONS = []

class DummyAdapter(Adapter):
    def __str__(self):
        return "dummy"

    def get_wrapper(self):
        from ..wrapper import ResourceWrapper

        return ResourceWrapper

    def load_from_id(self, resource_id, from_prefetch=None):
        return (
            from_prefetch(resource_id)
            if from_prefetch is not None
            else _DUMMY_STORE.get(resource_id)
        )

    def get_wkrm_definitions(self):
        return WKRM_DEFINITIONS
