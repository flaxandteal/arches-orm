import uuid
from typing import Any, Callable
from functools import cached_property
from django.contrib.auth.models import User
from arches.app.models.models import Node, ResourceInstance
from arches.app.models.tile import Tile
from arches.app.models.resource import Resource
from collections import UserDict

from arches_orm.view_models import (
    WKRI,
    UserViewModelMixin,
    UserProtocol,
    StringViewModel,
    RelatedResourceInstanceListViewModel,
    RelatedResourceInstanceViewModelMixin,
    ConceptListValueViewModel,
    ConceptValueViewModel,
    SemanticViewModel,
)

class RegisterFunction(Callable):
    def __init__(self, fn):
        self.fn = fn

    def __call__(self, *args, **kwargs):
        return self.fn(*args, **kwargs)

    def as_tile_data(self, as_tile_data_fn):
        self.as_tile_data_fn = as_tile_data_fn

    def transform_value_for_tile(self, value):
        return self.as_tile_data_fn(value)


class ViewModelRegister(UserDict):
    def __call__(self, typ):
        def wrapper(fn) -> RegisterFunction:
            self[typ] = RegisterFunction(fn)
            return self[typ]

        return wrapper

    @cached_property
    def _datatype_factory(self):
        """Caching datatype factory retrieval (possibly unnecessary)."""
        from arches.app.datatypes.datatypes import DataTypeFactory

        return DataTypeFactory()

    def make(
        self,
        tile: Tile,
        node: Node,
        value: Any = None,
        parent: Any = None,
        child_nodes: list = None,
    ):
        datatype = self._datatype_factory.get_instance(node.datatype)
        if node.datatype in self:
            registration = self[node.datatype]
            record = registration(tile, node, value, parent, child_nodes, datatype)
            return record, registration.transform_value_for_tile
        else:
            return datatype.transform_value_for_tile(
                value or tile.data, **(node.config or {})
            ), lambda value: datatype.transform_value_for_tile(
                value, **(node.config or {})
            )


def get_view_model_for_datatype(tile, node, parent, child_nodes, value=None):
    return REGISTER.make(
        tile, node, value=value, parent=parent, child_nodes=child_nodes
    )


REGISTER = ViewModelRegister()
