# MIT License
#
# Copyright (c) 2020 Taku Fukada, 2022 Phil Weir

import os
import graphene

from starlette.middleware import Middleware
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.responses import PlainTextResponse, JSONResponse
from starlette.routing import Route
from starlette.endpoints import HTTPEndpoint
from starlette_graphene3 import GraphQLApp, make_graphiql_handler
from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware

from starlette_context import plugins
from starlette_context.middleware import RawContextMiddleware
from starlette_context import context as starlette_context
from arches_orm.adapter import get_adapter

from .auth import BasicAuthBackend
from .resources import ResourceQuery, FullResourceMutation
from .concepts import ConceptQuery, FullConceptMutation
from .resource_models import ResourceModelQuery

class UnauthorizedException(Exception):
    ...

DEBUG = os.getenv("DEBUG", "False") == "True"

resources_schema = graphene.Schema(query=ResourceQuery, mutation=FullResourceMutation)
concept_schema = graphene.Schema(query=ConceptQuery, mutation=FullConceptMutation)
resource_model_schema = graphene.Schema(query=ResourceModelQuery)

class App(HTTPEndpoint):
    async def get(self, request):
        return PlainTextResponse("OK")

class ORMContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        with get_adapter().context(user=starlette_context.data["user"]) as _:
            return await call_next(request)

# TODO: More elegant solution, using the schema.
def admin_middleware(next_mw, root, info, **args):
    if starlette_context.data["user"].is_superuser:
        return next_mw(root, info, **args)
    else:
        raise UnauthorizedException()

middleware = [
    Middleware(
        RawContextMiddleware,
        plugins=(
            plugins.RequestIdPlugin(),
            plugins.CorrelationIdPlugin()
        )
    ),
    Middleware(AuthenticationMiddleware, backend=BasicAuthBackend()),
    Middleware(ORMContextMiddleware),
]

graphql_admin_middleware = [
    admin_middleware
]

app = Starlette(debug=DEBUG, routes=[Route("/", App)], middleware=middleware)
app.mount("/resources/", GraphQLApp(resources_schema, on_get=make_graphiql_handler()))
app.mount("/concepts/", GraphQLApp(concept_schema, on_get=make_graphiql_handler(), middleware=graphql_admin_middleware))
app.mount("/resource-models/", GraphQLApp(resource_model_schema, on_get=make_graphiql_handler(), middleware=graphql_admin_middleware))
