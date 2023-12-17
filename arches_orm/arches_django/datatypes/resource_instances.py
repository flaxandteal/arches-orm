import uuid
from arches.app.models.models import ResourceInstance
from arches.app.models.resource import Resource

from arches_orm.view_models import (
    WKRI,
    RelatedResourceInstanceListViewModel,
    RelatedResourceInstanceViewModelMixin,
)
from ._register import REGISTER


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
            datatype="resource-instance",
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
    from arches_orm.utils import (
        get_well_known_resource_model_by_graph_id,
        attempt_well_known_resource_model,
    )

    value = value or tile.data.get(str(node.nodeid))
    if isinstance(value, dict):
        value = value.get("resourceId")
    resource_instance_id = None
    resource_instance = None
    if isinstance(value, uuid.UUID | str):
        resource_instance_id = value
    else:
        resource_instance = value

    if not resource_instance:
        if resource_instance_id:
            resource_instance = attempt_well_known_resource_model(
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

    model_class_name = str(_resource_instance.__class__.__name__)
    mixin = RI_VIEW_MODEL_CLASSES.get(model_class_name)
    if not mixin:
        mixin = type(
            f"{model_class_name}RelatedResourceInstanceViewModel",
            (_resource_instance.__class__, RelatedResourceInstanceViewModelMixin),
            dict(proxy=True),
        )
        RI_VIEW_MODEL_CLASSES[model_class_name] = mixin
    _resource_instance.__class__ = mixin
    _resource_instance._cross_record = datum

    return _resource_instance


@resource_instance.as_tile_data
def ri_as_tile_data(_):
    return {}
    raise NotImplementedError()
