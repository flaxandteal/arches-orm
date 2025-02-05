import uuid
from typing import List

from arches_orm.view_models import (

<<<<<<< HEAD
    EmptyDomainValueViewModel,
    DomainListValueViewModel,
    DomainValueViewModel, 
    DomainOptions
)
from ._register import REGISTER
||||||| parent of ebd21e0 (feat(#36): added domains to its own file)
# @REGISTER("domain-value")
# def domain_value(tile, node, value: UUID | None, _, __, ___, datatype):
#     if value is None:
#         value = tile.data.get(str(node.nodeid), []) or []
=======
    EmptyConceptValueViewModel,
    DomainListValueViewModel,
    DomainValueViewModel, 
    DomainOptions
)
from arches_orm.collection import make_collection, CollectionEnum
from ._register import REGISTER
>>>>>>> ebd21e0 (feat(#36): added domains to its own file)

def make_domain_value(value: uuid.UUID | None, domain_options: DomainOptions | None, datatype: str):

<<<<<<< HEAD
    if value is None or isinstance(value, EmptyDomainValueViewModel):
        if domain_options:
            return EmptyDomainValueViewModel(
                value
            )
            return None
        return None
||||||| parent of ebd21e0 (feat(#36): added domains to its own file)
#     if node and node.config:
#         domain_options = node.config.get("options")
=======
    if value is None or isinstance(value, EmptyConceptValueViewModel):
        if domain_options:
            # return EmptyConceptValueViewModel(
            #     value,
>>>>>>> ebd21e0 (feat(#36): added domains to its own file)

<<<<<<< HEAD
    return DomainValueViewModel(
        value,
        domain_options,
        datatype
    )
||||||| parent of ebd21e0 (feat(#36): added domains to its own file)
#     return DomainValueViewModel(value, domain_options, datatype)
=======
            #     partial(retrieve_collection, datatype=datatype)
            # )
            return None
        return None
>>>>>>> ebd21e0 (feat(#36): added domains to its own file)

<<<<<<< HEAD
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
||||||| parent of ebd21e0 (feat(#36): added domains to its own file)
# @domain_value.as_tile_data
# def dv_as_tile_data(domain_value):
#     return domain_value.value
=======
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

    domain_options: DomainOptions | None = None

    def make_domain_value(value):
        return REGISTER.make(tile, node, value=value, datatype="domain-value")[0]

    if node and node.config:
        domain_options = node.config.get("options")

    return DomainListValueViewModel(value, make_domain_value)

@domain_value_list.as_tile_data
def dl_as_tile_data(domain_value_list):
    print('dvl_as_tile_data | ', domain_value_list)
    data = [dv_as_tile_data(domain_value) for domain_value in domain_value_list]  # Should be a list, not a set
    print('dvl_as_tile_data  data | ', data)
    return data
>>>>>>> ebd21e0 (feat(#36): added domains to its own file)
