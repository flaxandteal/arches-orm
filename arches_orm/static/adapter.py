from __future__ import annotations

import logging
from pathlib import Path
from enum import Enum
from uuid import UUID
from arches_orm.adapter import Adapter
from arches_orm.view_models.concepts import ConceptValueViewModel
from .wrapper import _STATIC_STORE
from .datatypes.concepts import (
    load_collection_path,
    load_concept_path,
    retrieve_collection,
    make_concept,
    retrieve_concept_value,
    save_concept,
    update_collections,
    build_collection
)

logger = logging.getLogger(__name__)


LOAD_FULL_NODE_OBJECTS = True
LOAD_ALL_NODES = True

WKRM_DEFINITIONS = []

class StaticAdapter(Adapter):

    key = "static"
    _collections_loaded = False

    def get_wrapper(self):
        from ..wrapper import ResourceWrapper

        return ResourceWrapper

    def update_collections(self, concept: ConceptValueViewModel, source_file: Path) -> None:
        update_collections(concept, source_file, arches_url=self.config["arches_url"])

    def save_concept(self, concept: ConceptValueViewModel, output_file: Path | None) -> None:
        save_concept(concept, output_file, arches_url=self.config["arches_url"])

    def retrieve_concept_value(self, concept_id: str | UUID) -> ConceptValueViewModel:
        return retrieve_concept_value(concept_id)

    def make_concept(self, concept_id: str | UUID, values: dict[UUID, tuple[str, str]], children: list[UUID] | None) -> ConceptValueViewModel:
        return make_concept(concept_id, values, children)

    def derive_collection(self, collection_id: str | UUID, include: list[UUID] | None, exclude: list[UUID] | None, language: str | None=None) -> type[Enum]:
        """Note that include and exclude should be lists of concept, not value, IDs."""
        return build_collection(collection_id, include=include, exclude=exclude, language=language)

    def get_collection(self, collection_id: str | UUID) -> type[Enum]:
        if not self._collections_loaded:
            for concept_path in self.config["concept_paths"]:
                load_concept_path(concept_path)
                load_collection_path(concept_path)
        return retrieve_collection(collection_id)

    def load_from_id(self, resource_id, from_prefetch=None):
        return (
            from_prefetch(resource_id)
            if from_prefetch is not None
            else _STATIC_STORE.get(resource_id)
        )

    def get_wkrm_definitions(self):
        return WKRM_DEFINITIONS
