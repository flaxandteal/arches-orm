from typing import Protocol
import uuid
from collections import UserList
from ._base import (
    ViewModel,
)

class ResourceProtocol(Protocol):
    graphid: uuid.UUID
    _cross_record: dict | None = None


class RelatedResourceInstanceViewModelMixin(ViewModel):
    """Wraps a resource instance.

    Subclasses str, so it can be handled like a string enum, but keeps
    the `.value`, `.lang` and `.text` properties cached, so you can
    find out more.
    """

    def get_relationships(self):
        # TODO: nesting
        return [self]


class RelatedResourceInstanceListViewModel(UserList, ViewModel):
    """Wraps a concept list, allowing interrogation.

    Subclasses list, so its members can be handled like a string enum, but keeps
    the `.value`, `.lang` and `.text` properties cached, so you can
    find out more.
    """

    def __init__(
        self,
        parent_wkri,
        resource_instance_list,
        make_ri_cb,
    ):
        self._parent_wkri = parent_wkri
        self._make_ri_cb = make_ri_cb
        for resource_instance in resource_instance_list:
            self.append(resource_instance)

    def append(self, item: str | uuid.UUID | ResourceProtocol):
        """Add a well-known resource to the list."""

        if isinstance(item, RelatedResourceInstanceViewModelMixin):
            raise NotImplementedError("Cannot currently reparent related resources")

        resource_instance = item if isinstance(item, ResourceProtocol) else None
        resource_instance_id = item if isinstance(item, str | uuid.UUID) else None

        value = self._make_ri_cb(resource_instance or resource_instance_id)
        if str(value._cross_record["wkriFrom"]) != str(self._parent_wkri.id):
            raise NotImplementedError("Cannot current reparent related resources")

        return super().append(item)

    def remove(self, value):
        for item in self:
            if value.resourceinstanceid == item.resourceinstanceid:
                value = item
        super().remove(value)

    def get_relationships(self):
        return sum((x.get_relationships() for x in self), [])
