import uuid
from collections import UserList
from ._base import ViewModel, WKRI


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

    def append(self, item: str | uuid.UUID | WKRI):
        """Add a well-known resource to the list."""

        if isinstance(item, RelatedResourceInstanceViewModelMixin):
            raise NotImplementedError("Cannot currently reparent related resources")

        resource_instance = None
        resource_instance_id = None
        if isinstance(item, WKRI):
            resource_instance = item
        elif isinstance(item, str | uuid.UUID):
            resource_instance_id = item
        elif isinstance(item, dict) and "resourceId" in item:
            resource_instance_id = item["resourceId"]

        value, _, __, ___ = self._make_ri_cb(resource_instance or resource_instance_id)

        if not value:
            raise RuntimeError(f"Could not append {item} to resource list within {self._parent_wkri}")
        if str(value._cross_record["wkriFrom"].id) != str(self._parent_wkri.id):
            raise NotImplementedError("Cannot currently reparent related resources")

        return super().append(value)

    def remove(self, value):
        for item in self:
            if value.resourceinstanceid == item.resourceinstanceid:
                value = item
        super().remove(value)
