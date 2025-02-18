import uuid
from uuid import UUID
import logging
from enum import Enum
from typing import List

from arches_orm.view_models import (

    EmptyDomainValueViewModel,
    DomainListValueViewModel,
    DomainValueViewModel, 
    DomainOption,
    get_domain_enum,
    make_domain_enum,
    DomainValue,
)
from ._register import REGISTER

def make_domain_value(node, value: uuid.UUID | None):
    if not (enum := get_domain_enum(node.nodeid)):
        domain_options = node.config.get("options")
        if not domain_options:
            logging.warn("Missing node options for domain value: {}", str(node.nodeid))

        if value is None or isinstance(value, EmptyDomainValueViewModel):
            return None

        options = [DomainValueViewModel(
            node.nodeid,
            DomainOption(option),
        ) for option in domain_options]

        enum = make_domain_enum(
            node.alias,
            options,
            node.nodeid
        )

    if not value:
        selected = EmptyDomainValueViewModel(
            node.nodeid,
        )
        if enum:
            selected = enum.__selected__ or selected
        return selected

    if isinstance(value, UUID):
        return enum.__domain_values__[value]
    else:
        return enum[value]

@REGISTER("domain-value")
def domain_value(tile, node, value: uuid.UUID | None, _, __, ___, datatype) -> DomainValueViewModel:
    if value is None:
        value = tile.data.get(str(node.nodeid), []) or []

    if not node:
        return None

    if isinstance(value, Enum):
        value = value.value

    if isinstance(value, DomainValue):
        return value

    if value and not isinstance(value, UUID):
        try:
            value = UUID(value)
        except ValueError:
            ...

    # print(node)
    return make_domain_value(node, value)

@domain_value.as_tile_data
def dv_as_tile_data(domain_value):
    if not domain_value:
        return None
    if isinstance(domain_value, Enum):
        domain_value = domain_value.value
    return domain_value._domain_option["id"]

@REGISTER("domain-value-list")
def domain_value_list(tile, node, value: List[uuid.UUID] | None, _, __, ___, datatype):
    # print('TILE |  ', tile)
    # print('node |  ', node)
    # print('value |  ', value)
    # print('_ |  ', _)
    # print('__ |  ', __)
    # print('__ |  ', __)
    # print('___ |  ', ___)
    # print('datatype |  ', datatype)

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
