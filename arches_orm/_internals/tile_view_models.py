from typing import Any, Callable
import uuid
from functools import cached_property
from django.contrib.auth.models import User
from arches.app.models.models import Node, ResourceInstance
from arches.app.models.tile import Tile
from arches.app.models.resource import Resource
from collections import UserDict

from .view_models import (
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


@REGISTER("resource-instance-list")
def resource_instance_list(
    tile,
    node,
    value: uuid.UUID | str | WKRI | Resource | ResourceInstance | None,
    parent,
    child_nodes,
    datatype,
):
    def make_ri_cb(value):
        return REGISTER.make(
            tile,
            node,
            value=value,
            parent=parent,
            child_nodes=child_nodes,
        )

    return RelatedResourceInstanceListViewModel(
        parent,
        value,
        make_ri_cb,
    )


@resource_instance_list.as_tile_data
def ril_as_tile_data(resource_instance_list):
    return [x.as_tile_data() for x in resource_instance_list]


RI_VIEW_MODEL_CLASSES = {}


@REGISTER("resource-instance")
def resource_instance(
    tile,
    node,
    value: uuid.UUID | str | WKRI | Resource | ResourceInstance | None,
    parent_wkri,
    child_nodes,
    resource_instance_datatype,
):
    from .utils import (
        get_well_known_resource_model_by_graph_id,
        attempt_well_known_resource_model,
    )

    if value is None:
        raise NotImplementedError()
    resource_instance_id = None
    resource_instance = None
    if isinstance(value, uuid.UUID | str):
        resource_instance_id = value
    else:
        resource_instance = value

    if not resource_instance:
        if resource_instance_id:
            _resource_instance = attempt_well_known_resource_model(
                resource_instance_id, related_prefetch=parent_wkri._related_prefetch
            )
        else:
            raise RuntimeError("Must pass a resource instance or ID")

    if not isinstance(resource_instance, WKRI):
        wkrm = get_well_known_resource_model_by_graph_id(
            resource_instance.graph_id, default=None
        )
        if wkrm:
            _resource_instance = wkrm.from_resource(resource_instance)
        else:
            raise RuntimeError("Cannot adapt unknown resource model")
    else:
        _resource_instance = resource_instance

    if _resource_instance is None:
        raise RuntimeError("Could not normalize resource instance")

    datum = {}
    datum["wkriFrom"] = parent_wkri
    datum[
        "wkriFromKey"
    ] = node.alias  # FIXME: we should use the ORM key to be consistent
    datum["wkriFromNodeid"] = node.nodeid
    datum["wkriFromTile"] = tile
    datum["datatype"] = resource_instance_datatype

    if _resource_instance._cross_record and _resource_instance._cross_record != datum:
        raise NotImplementedError("Cannot currently reparent a resource instance")

    mixin = RI_VIEW_MODEL_CLASSES.get(_resource_instance.model_class_name)
    if not mixin:
        mixin = type(
            f"{_resource_instance.model_class_name}RelatedResourceInstanceViewModel",
            (_resource_instance.__class__, RelatedResourceInstanceViewModelMixin),
            {},
        )
        RI_VIEW_MODEL_CLASSES[_resource_instance.model_class_name] = mixin
    _resource_instance.__class__ = mixin
    _resource_instance._cross_record = datum

    return _resource_instance


@resource_instance.as_tile_data
def ri_as_tile_data(_):
    raise NotImplementedError()


@REGISTER("concept-list")
def concept_list(tile, node, value: list[uuid.UUID | str] | None, _, __):
    if value is not None:
        tile.data = value
    make_cb = REGISTER.make(tile, node, value=value)
    return ConceptListValueViewModel(tile.data, make_cb)


@concept_list.as_tile_data
def cl_as_tile_data(concept_list):
    return [x.as_tile_data() for x in concept_list]


@REGISTER("concept")
def concept_value(tile, node, value: uuid.UUID | str | None, __, ___, datatype):
    if value is not None:
        tile.data[str(node.nodeid)] = value
    concept_value_cb = datatype.get_value
    if tile.data[str(node.nodeid)] is None:
        return None
    return ConceptValueViewModel(tile.data[str(node.nodeid)], concept_value_cb)


@concept_value.as_tile_data
def cv_as_tile_data(concept_value):
    return str(concept_value._concept_value_id)


@REGISTER("string")
def string(tile, node, value: dict | None, _, __, string_datatype):
    tile.data.setdefault(str(node.nodeid), {})
    if value is not None:
        if isinstance(value, dict):
            tile.data[str(node.nodeid)].update(value)
        else:
            tile.data[str(node.nodeid)] = string_datatype.transform_value_for_tile(
                value
            )

    def _flatten_cb(value, language):
        tile.data[str(node.nodeid)] = tile.data[str(node.nodeid)] or {}
        tile.data[str(node.nodeid)].update(value)
        return string_datatype.get_display_value(tile, node, language=language)

    if tile.data[str(node.nodeid)] is None:
        return None
    return StringViewModel(tile.data[str(node.nodeid)], _flatten_cb)


@string.as_tile_data
def s_as_tile_data(string):
    return string._value


class UserViewModel(User, UserViewModelMixin):
    class Meta:
        proxy = True
        app_label = "arches-orm"
        db_table = User.objects.model._meta.db_table


@REGISTER("user")
def user(tile, node, value, _, __, user_datatype) -> UserProtocol:
    user = None
    value = value or tile.data.get(str(node.nodeid))
    if value:
        if isinstance(value, User):
            if value.pk:
                value = value.pk
            else:
                user = UserViewModel()
                user.__dict__.update(value.__dict__)
        if value:
            user = UserViewModel.objects.get(pk=int(value))
    if not user:
        user = UserViewModel()
    return user


@user.as_tile_data
def u_as_tile_data(view_model):
    return view_model.pk


@REGISTER("semantic")
def semantic(
    tile,
    node,
    value: uuid.UUID | str | WKRI | Resource | ResourceInstance | None,
    parent,
    child_nodes,
    datatype,
):
    def make_pseudo_node(key):
        return parent._make_pseudo_node(
            key,
            tile=(tile if child_nodes[key][1] else None),  # Does it share a tile
        )

    return SemanticViewModel(
        parent,
        {key: value[1] for key, value in child_nodes.items()},
        value,
        make_pseudo_node,
    )


@semantic.as_tile_data
def sm_as_tile_data(semantic):
    # Ensure all nodes have populated the tile
    tile = None
    for value in semantic.get_children(direct=True):
        tile = value.get_tile() or tile
    data = tile.data if tile is not None else {}
    return data
