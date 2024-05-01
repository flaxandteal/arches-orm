from typing import Any
from django.dispatch import receiver
from django.db.models.signals import post_delete, post_save, post_init
from arches.app.models.tile import Tile
from arches.app.models.models import ResourceXResource, ResourceInstance, GraphModel
from copy import deepcopy

from arches_orm.wkrm import get_well_known_resource_model_by_graph_id


@receiver(post_init, sender=Tile)
def check_resource_instance_on_tile_capture(sender, instance, **kwargs):
    instance._original_data = None
    if instance.data:
        instance._original_data = deepcopy(instance.data)
    # This happens (briefly) as a result of Arches creating a Tile (arches/app/views/tile.py:138) with a dict
    # and calling super in the model.
    elif instance.tileid and isinstance(instance.tileid, dict) and "_original_data" in instance.tileid:
        instance._original_data = deepcopy(instance.tileid["_original_data"])

@receiver(post_save, sender=Tile)
def check_resource_instance_on_tile_save(sender, instance, **kwargs):
    """Catch saves on tiles for resources."""
    if instance.data:
        seen = set()
        if hasattr(instance, "_original_data") and instance._original_data:
            for key, original_values in instance._original_data.items():
                if not isinstance(original_values, list):
                    original_values = [original_values]
                for value in original_values:
                    if value and isinstance(value, dict):
                        # If resourceXresourceId is unset, then this may only be a temporary value, from
                        # arches/app/views/tile.py:136 Tile(data)
                        # TODO: confirm behaviour with save_crosses=True
                        if value.get("resourceXresourceId") and (rto_id := value.get("resourceId")):
                            seen.add((key, rto_id))

        for key, values in instance.data.items():
            if values:
                if not isinstance(values, list):
                    values = [values]
                for value in values:
                    if value and isinstance(value, dict):
                        # Should always be a resourceXresourceId when this is saved.
                        if (rXr_id := value.get("resourceXresourceId")) and (rto_id := value.get("resourceId")):
                            if (key, rto_id) in seen:
                                seen.remove((key, rto_id))
                            else:
                                # TODO: inefficient
                                rto = ResourceInstance.objects.get(resourceinstanceid=rto_id)
                                if rto:
                                    relationship = ResourceXResource(
                                        resourcexid=rXr_id,
                                        resourceinstanceidfrom=instance.resourceinstance,
                                        resourceinstanceidto=rto,
                                        resourceinstancefrom_graphid=instance.resourceinstance.graph,
                                        resourceinstanceto_graphid=rto.graph
                                    )
                                    if relationship.resourceinstanceto_graphid:
                                        check_related_to(sender, relationship, "relationship saved", tile=instance, nodeid=key, **kwargs)
        for key, rto_id in seen:
            rto = ResourceInstance.objects.get(resourceinstanceid=rto_id)
            if rto:
                relationship = ResourceXResource(
                    resourceinstanceidfrom=instance.resourceinstance,
                    resourceinstanceidto=rto,
                    resourceinstancefrom_graphid=instance.resourceinstance.graph,
                    resourceinstanceto_graphid=rto.graph
                )
                if relationship.resourceinstanceto_graphid:
                    check_related_to(sender, relationship, "relationship deleted", tile=instance, nodeid=key, **kwargs)
    if instance.resourceinstance and instance.resourceinstance.resourceinstanceid:
        check_resource_instance(sender, instance, "tile saved", **kwargs)


@receiver(post_delete, sender=Tile)
def check_resource_instance_on_tile_delete(sender, instance, **kwargs):
    """Catch deletions on tiles for resources."""
    if instance.resourceinstance and instance.resourceinstance.resourceinstanceid:
        check_resource_instance(sender, instance, "tile deleted", **kwargs)


@receiver(post_delete, sender=ResourceXResource)
def check_resource_instance_on_related_to_delete(sender, instance, **kwargs):
    """Catch deletions on tiles for resources."""
    if instance.resourceinstanceto_graphid:
        check_related_to(sender, instance, "relationship deleted", **kwargs)

def check_related_to(sender: type[ResourceInstance], instance: ResourceXResource, reason: str, tile = None, nodeid = None, **kwargs: Any) -> None:
    graph_id_from = (
        instance.resourceinstancefrom_graphid.graphid
        if isinstance(instance.resourceinstancefrom_graphid, GraphModel) else
        instance.resourceinstancefrom_graphid.graphid
    )
    graph_id_to = (
        instance.resourceinstanceto_graphid.graphid
        if isinstance(instance.resourceinstanceto_graphid, GraphModel) else
        instance.resourceinstanceto_graphid.graphid
    )
    model_cls_from = None
    model_cls_to = None
    if graph_id_from:
        model_cls_from = get_well_known_resource_model_by_graph_id(
            graph_id_from
        )
    if graph_id_to:
        model_cls_to = get_well_known_resource_model_by_graph_id(
            graph_id_to
        )
    if (model_cls_to and model_cls_to.post_related_to.has_listeners()) or (model_cls_from and model_cls_from.post_related_from.has_listeners()):
        resource_instance_from = None
        resource_instance_to = None
        if model_cls_from and instance.resourceinstanceidfrom:
            resource_instance_from = model_cls_from.from_resource_instance(instance.resourceinstanceidfrom)
        if model_cls_to and instance.resourceinstanceidto:
            resource_instance_to = model_cls_to.from_resource_instance(instance.resourceinstanceidto)

        if model_cls_to and resource_instance_to:
            model_cls_to.post_related_to.send(
                model_cls_to, resource_instance_to=resource_instance_to, resource_instance_from=resource_instance_from, relationship=instance, reason=reason, tile=tile, nodeid=nodeid
            )
        if model_cls_from and resource_instance_from:
            model_cls_from.post_related_from.send(
                model_cls_from, resource_instance_to=resource_instance_to, resource_instance_from=resource_instance_from, relationship=instance, reason=reason, tile=tile, nodeid=nodeid
            )


def check_resource_instance(sender, instance, reason, **kwargs):
    """On an action against a tile, emit a post_save signal for the
    well-known resource.
    """
    # This (I think) gets loaded anyway during the Tile save
    model_cls = get_well_known_resource_model_by_graph_id(
        instance.resourceinstance.graph_id
    )
    if model_cls and model_cls.post_save.has_listeners():
        resource_instance = model_cls.from_resource_instance(instance.resourceinstance)
        model_cls.post_save.send(
            model_cls, instance=resource_instance, reason=reason, tile=instance
        )


HOOKS = {"post_init", "post_save", "post_delete"}
