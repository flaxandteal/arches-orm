import uuid
from typing import List

from arches_orm.view_models import (

    EmptyDomainValueViewModel,
    DomainListValueViewModel,
    DomainValueViewModel, 
    DomainOptions
)
from ._register import REGISTER

def make_domain_value(value: uuid.UUID | None, domain_options: DomainOptions | None, datatype: str):

    if value is None or isinstance(value, EmptyDomainValueViewModel):
        if domain_options:
            return EmptyDomainValueViewModel(
                value
            )
            return None
        return None

    return DomainValueViewModel(
        value,
        domain_options,
        datatype
    )

@REGISTER("domain-value")
def domain_value(tile, node, value: uuid.UUID | None, _, __, ___, datatype) -> DomainValueViewModel:
    if value is None:
        value = tile.data.get(str(node.nodeid), []) or []

    domain_options: DomainOptions | None = None

    if node and node.config:
        domain_options = node.config.get("options")

    return make_domain_value(value, domain_options, datatype)

@domain_value.as_tile_data
def dv_as_tile_data(domain_value):
    return domain_value.value

@REGISTER("domain-value-list")
def domain_value_list(tile, node, value: List[uuid.UUID] | None, _, __, ___, datatype):
    # * We check if the value is set, if not we reterieve the value from a tile
    if value is None or not value:
        value = tile.data.get(str(node.nodeid), []) or []

    def make_domain_value(value: uuid.UUID):
        return REGISTER.make(tile, node, value=value, datatype="domain-value")[0]

    return DomainListValueViewModel(value, make_domain_value)

@domain_value_list.as_tile_data
def dl_as_tile_data(domain_value_list):
    data = [dv_as_tile_data(domain_value) for domain_value in domain_value_list]  # Should be a list, not a set
    return data
