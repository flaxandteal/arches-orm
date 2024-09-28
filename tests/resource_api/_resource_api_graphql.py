from arches_orm.utils import add_custom_datatype

add_custom_datatype("TM65CENTREPOINT", "tm65centrepoint")

from ._datatypes import tm65

from arches_orm.graphql.resource_api_asgi import app
