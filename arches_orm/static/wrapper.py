import logging
from arches_orm.wrapper import ResourceWrapper


logger = logging.getLogger(__name__)

_STATIC_STORE = {}


class StaticResourceWrapper(ResourceWrapper, proxy=True):
    """Static wrapper for all well-known resources.

    When you use, `Person`, etc. it will be this class in disguise.
    """

    def _add_events(cls) -> None:
        """Add events to this model."""
        return

    def search(cls, text, fields=None, _total=None) -> tuple[list[int], int]:
        """Search for resources of this model, and return as well-known resources."""
        results = []
        return results, len(results)

    def all_ids(cls) -> list[str]:
        """Get IDs for all resources of this type."""
        return [
            resource.id for resource in cls.all()
        ]

    def all(cls, related_prefetch=None) -> list["StaticResourceWrapper"]:
        """Get all resources of this type."""
        return [
            resource
            for id, resource in _STATIC_STORE.items()
            if resource.__class__ == cls
        ]

    def find(cls, resourceinstanceid):
        """Find an individual well-known resource by instance ID."""
        return _STATIC_STORE[resourceinstanceid]

    def delete(self):
        """Delete the underlying resource."""
        del _STATIC_STORE[self.id]

    def remove(self):
        """When called via a relationship (dot), remove the relationship."""

    def append(self, _no_save=False):
        """When called via a relationship (dot), append to the relationship."""

    def where(cls, cross_record=None, **kwargs):
        """Do a filtered query returning a list of well-known resources."""

    def get_adapter():
        """Get the adapter that encapsulates this wrapper."""

    def reload(self, ignore_prefetch=True):
        """Reload field values, but not node values for class."""

    def get_root(self):
        """Get the root value."""
