from __future__ import annotations

import logging
from pathlib import Path
from enum import Enum
from uuid import UUID
from arches_orm.adapter import Adapter
from arches_orm.view_models.concepts import ConceptValueViewModel
from .datatypes.concepts import load_collection_path, load_concept_path, retrieve_collection, make_concept, retrieve_concept, save_concept, update_collections
from .datatypes.resource_models import load_models
from .datatypes.resource_instances import STATIC_STORE

logger = logging.getLogger(__name__)


LOAD_FULL_NODE_OBJECTS = True
LOAD_ALL_NODES = True

WKRM_DEFINITIONS = []

class ResourceAPIAdapter(Adapter):

    key = "resource_api"
    _collections_loaded = False
    _wkrm_definitions_loaded = False

    def get_wrapper(self):
        from .wrapper import ResourceAPIResourceWrapper

        return ResourceAPIResourceWrapper

    def update_collections(self, concept: ConceptValueViewModel, source_file: Path) -> None:
        update_collections(concept, source_file, arches_url=self.config["arches_url"])

    def save_concept(self, concept: ConceptValueViewModel, output_file: Path | None) -> None:
        save_concept(concept, output_file, arches_url=self.config["arches_url"])

    def retrieve_concept(self, concept_id: str | UUID) -> ConceptValueViewModel:
        return retrieve_concept(concept_id)

    def make_concept(self, concept_id: str | UUID, values: dict[UUID, tuple[str, str]], children: list[UUID] | None) -> ConceptValueViewModel:
        return make_concept(concept_id, values, children)

    def get_collection(self, collection_id: str) -> type[Enum]:
        if not self._collections_loaded:
            for concept_path in self.config["concept_paths"]:
                load_concept_path(concept_path)
                load_collection_path(concept_path)
        return retrieve_collection(collection_id)

    def load_from_id(self, resource_id, from_prefetch=None, lazy=False):
        from arches_orm.wkrm import get_resource_models_for_adapter
        static_resource = (
            from_prefetch(resource_id)
            if from_prefetch is not None
            else STATIC_STORE[resource_id]
        )
        resource_models_by_graph_id = get_resource_models_for_adapter(self.key)[
            "by-graph-id"
        ]
        if static_resource.graph_id not in resource_models_by_graph_id:
            logger.error("Tried to load non-existent WKRM: %s", resource_id)
            return None
        return resource_models_by_graph_id[static_resource.graph_id].from_static_resource(
            static_resource, related_prefetch=from_prefetch, lazy=lazy
        )

    def get_wkrm_definitions(self):
        global WKRM_DEFINITIONS
        if not self._wkrm_definitions_loaded:
            WKRM_DEFINITIONS = load_models()
        return WKRM_DEFINITIONS
