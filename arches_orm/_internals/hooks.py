from django.dispatch import receiver
from django.db.models.signals import post_delete, post_save
from arches.app.models.tile import Tile

from .utils import get_well_known_resource_model_by_graph_id


@receiver(post_save, sender=Tile)
def check_resource_instance_on_tile_save(sender, instance, **kwargs):
    """Catch saves on tiles for resources."""
    if instance.resourceinstance and instance.resourceinstance.resourceinstanceid:
        check_resource_instance(sender, instance, "tile saved", **kwargs)


@receiver(post_delete, sender=Tile)
def check_resource_instance_on_tile_delete(sender, instance, **kwargs):
    """Catch deletions on tiles for resources."""
    if instance.resourceinstance and instance.resourceinstance.resourceinstanceid:
        check_resource_instance(sender, instance, "tile deleted", **kwargs)


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
