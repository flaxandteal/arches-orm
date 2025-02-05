# from uuid import UUID
# from ._register import REGISTER
# from arches_orm.view_models.domains import DomainValueViewModel, DomainOptions

# def make_domain_value(value: UUID | None, options: DomainOptions | None, datatype: str):
#     return DomainValueViewModel(
#         value,
#         options,
#         datatype
#     )

# @REGISTER("domain-value")
# def domain_value(tile, node, value: UUID | None, _, __, ___, datatype):
#     if value is None:
#         value = tile.data.get(str(node.nodeid), []) or []

#     domain_options = None

#     if node and node.config:
#         domain_options = node.config.get("options")

#     return DomainValueViewModel(value, domain_options, datatype)

# @domain_value.as_tile_data
# def dv_as_tile_data(domain_value):
#     return domain_value.value