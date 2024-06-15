import uuid
import logging
from collections import UserList
from arches.app.models.resource import Resource
from ._base import ViewModel, ResourceInstanceViewModel


class RelatedResourceInstanceViewModelMixin(ViewModel):
    """Wraps a resource instance."""


class RelatedResourceInstanceListViewModel(UserList, ViewModel):
    """Wraps a resource list, allowing interrogation."""

    def __init__(
        self,
        parent_wkri,
        resource_instance_list,
        make_ri_cb,
    ):
        super().__init__()
        self._parent_wkri = parent_wkri
        self._make_ri_cb = make_ri_cb
        if resource_instance_list:
            for resource_instance in resource_instance_list:
                self.append(resource_instance)

    def append(self, item: str | uuid.UUID | ResourceInstanceViewModel):
        """Add a well-known resource to the list."""

        if isinstance(item, RelatedResourceInstanceViewModelMixin):
            raise NotImplementedError("Cannot currently reparent related resources")

        resource_instance = None
        resource_instance_id = None
        if isinstance(item, ResourceInstanceViewModel):
            resource_instance = item
        elif isinstance(item, str | uuid.UUID):
            resource_instance_id = item
        elif isinstance(item, dict) and "resourceId" in item:
            resource_instance_id = item["resourceId"]
        # TODO: why no error on else?

        try:
            value, _, __, ___ = self._make_ri_cb(resource_instance or resource_instance_id)
        except Resource.DoesNotExist as exc:
            logging.error(
                "Tried to load %s for %s but could not: %s",
                str(resource_instance or resource_instance_id),
                str(self._parent_wkri.id if self._parent_wkri else "(unknown)"),
                str(exc)
            )
            value = None

        if not value:
            raise RuntimeError(f"Could not append {item} to resource list within {self._parent_wkri}")
        if str(value._._cross_record["wkriFrom"].id) != str(self._parent_wkri.id):
            raise NotImplementedError("Cannot currently reparent related resources")

        return super().append(value)

    def remove(self, value):
        for item in self:
            if value._.resourceinstanceid == item.resourceinstanceid:
                value = item
        super().remove(value)
