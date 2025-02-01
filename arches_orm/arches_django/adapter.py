import logging
import uuid
from enum import Enum
from rdflib.term import Node
from arches_orm.adapter import PseudoNodeAdapterMixin, Adapter
from arches_orm.view_models.concepts import ConceptValueViewModel

logger = logging.getLogger(__name__)


LOAD_FULL_NODE_OBJECTS = True
LOAD_ALL_NODES = True


class ArchesDjangoAdapter(Adapter, PseudoNodeAdapterMixin):
    # config:
    #   save_crosses: bool
    #      whether to save, or cache, resourceXresource models explicitly
    #      or leave it for Postgres

    key = "arches-django"

    def get_wrapper(self):
        from .wrapper import ArchesDjangoResourceWrapper

        return ArchesDjangoResourceWrapper

    def get_collection(self, collection_id: str) -> type[Enum]:
        from .datatypes.concepts import retrieve_collection
        return retrieve_collection(collection_id)

    def load_from_ids(self, resource_ids, from_prefetch=None, lazy=False):
        from arches_orm.wkrm import get_resource_models_for_adapter
        from arches.app.models.resource import Resource

        # Note that this will load an unpermissioned resource before
        # checking resources. This may be avoidable...
        resources = (
            (from_prefetch(resource_id) for resource_id in resource_ids)
            if from_prefetch is not None
            else Resource.objects.filter(pk__in=resource_ids)
        )
        for resource in resources:
            resource_models_by_graph_id = get_resource_models_for_adapter(self.key)[
                "by-graph-id"
            ]
            if str(resource.graph_id) not in resource_models_by_graph_id:
                logger.error("Tried to load non-existent WKRM: %s", resource.pk)
                return None
            yield resource_models_by_graph_id[str(resource.graph_id)].from_resource(
                resource, related_prefetch=from_prefetch, lazy=lazy
            )

    def load_from_id(self, resource_id, from_prefetch=None, lazy=False):
        from arches_orm.wkrm import get_resource_models_for_adapter
        from arches.app.models.resource import Resource

        # Note that this will load an unpermissioned resource before
        # checking resources. This may be avoidable...
        resource = (
            from_prefetch(resource_id)
            if from_prefetch is not None
            else Resource.objects.get(pk=resource_id)
        )
        resource_models_by_graph_id = get_resource_models_for_adapter(self.key)[
            "by-graph-id"
        ]
        if str(resource.graph_id) not in resource_models_by_graph_id:
            logger.error("Tried to load non-existent WKRM: %s", resource_id)
            return None
        return resource_models_by_graph_id[str(resource.graph_id)].from_resource(
            resource, related_prefetch=from_prefetch, lazy=lazy
        )

    def get_hooks(self):
        from .hooks import HOOKS

        return HOOKS

    def derive_collection(self, collection_id: str | uuid.UUID, include: list[uuid.UUID] | None=None, exclude: list[uuid.UUID] | None=None, language: str | None=None) -> type[Enum]:
        raise NotImplementedError()

    def get_concepts_by_label(self, label: str, pref_label_only: bool=False) -> list[ConceptValueViewModel]:
        raise NotImplementedError()

    def get_collections_by_label(self, label: str, pref_label_only: bool=False) -> list[type[Enum]]:
        raise NotImplementedError()

    def get_wkrm_definitions(self):
        from django.conf import settings
        return settings.WELL_KNOWN_RESOURCE_MODELS

    def make_concept(self, concept_id: str | uuid.UUID, values: dict[uuid.UUID, tuple[str, str, Node]], children: list[uuid.UUID] | None) -> ConceptValueViewModel:
        raise NotImplementedError()
