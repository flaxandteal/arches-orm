from typing import Any
from django.dispatch import receiver
from django.db.models.signals import post_delete, post_save
from arches.app.models.tile import Tile
from arches.app.models.models import ResourceXResource, ResourceInstance, GraphModel

from arches_orm.wkrm import get_well_known_resource_model_by_graph_id, attempt_well_known_resource_model


@receiver(post_save, sender=Tile)
def check_resource_instance_on_tile_save(sender, instance, **kwargs):
    """Catch saves on tiles for resources."""
    if instance.data:
        for key, values in instance.data.items():
            print(values, key)
            if values:
                if not isinstance(values, list):
                    values = [values]
                for value in values:
                    if value and isinstance(value, dict):
                        print(value, "VALUE")
                        if (rXr_id := value.get("resourceXresourceId")) and (rto_id := value.get("resourceId")):
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
                                    check_related_to(sender, relationship, "relationship-to saved", tile=instance, nodeid=key, **kwargs)
    if instance.resourceinstance and instance.resourceinstance.resourceinstanceid:
        check_resource_instance(sender, instance, "tile saved", **kwargs)


@receiver(post_delete, sender=Tile)
def check_resource_instance_on_tile_delete(sender, instance, **kwargs):
    """Catch deletions on tiles for resources."""
    if instance.resourceinstance and instance.resourceinstance.resourceinstanceid:
        check_resource_instance(sender, instance, "tile deleted", **kwargs)


@receiver(post_save, sender=ResourceXResource)
def check_resource_instance_on_related_to_save(sender, instance, **kwargs):
    """Catch saves on tiles for resources."""
    if instance.resourceinstanceto_graphid:
        check_related_to(sender, instance, "relationship-to saved", **kwargs)

@receiver(post_delete, sender=ResourceXResource)
def check_resource_instance_on_related_to_delete(sender, instance, **kwargs):
    """Catch deletions on tiles for resources."""
    if instance.resourceinstanceto_graphid:
        check_related_to(sender, instance, "relationship-to deleted", **kwargs)

def check_related_to(sender: type[ResourceInstance], instance: ResourceXResource, reason: str, tile = None, nodeid = None, **kwargs: Any) -> None:
    graph_id = (
        instance.resourceinstanceto_graphid.graphid
        if isinstance(instance.resourceinstanceto_graphid, GraphModel) else
        instance.resourceinstanceto_graphid.graphid
    )
    if graph_id:
        model_cls = get_well_known_resource_model_by_graph_id(
            graph_id
        )
        if model_cls and model_cls.post_related_to.has_listeners() and instance.resourceinstanceidto:
            resource_instance_to = model_cls.from_resource_instance(instance.resourceinstanceidto)
            resource_instance_from = None
            graph_id_from = (
                instance.resourceinstancefrom_graphid.graphid
                if isinstance(instance.resourceinstancefrom_graphid, GraphModel) else
                instance.resourceinstancefrom_graphid.graphid
            )
            if graph_id_from:
                model_cls_from = get_well_known_resource_model_by_graph_id(
                    graph_id_from
                )
                if model_cls_from and instance.resourceinstanceidfrom:
                    resource_instance_from = model_cls_from.from_resource_instance(instance.resourceinstanceidfrom)
            model_cls.post_related_to.send(
                model_cls, resource_instance_to=resource_instance_to, resource_instance_from=resource_instance_from, relationship=instance, reason=reason, tile=tile, nodeid=nodeid
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


HOOKS = {"post_save", "post_delete"}
