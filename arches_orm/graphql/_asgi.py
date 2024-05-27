# MIT License
#
# Copyright (c) 2020 Taku Fukada, 2022 Phil Weir

import os
import graphene

from starlette.middleware import Middleware
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.responses import PlainTextResponse
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

DEBUG = os.getenv("DEBUG", "False") == "True"

resources_schema = graphene.Schema(query=ResourceQuery, mutation=FullResourceMutation)

class App(HTTPEndpoint):
    async def get(self, request):
        return PlainTextResponse("OK")

class ORMContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        with get_adapter().context(user=starlette_context.data["user"]) as _:
            return await call_next(request)
middleware = [
    Middleware(
        RawContextMiddleware,
        plugins=(
            plugins.RequestIdPlugin(),
            plugins.CorrelationIdPlugin()
        )
    ),
    Middleware(AuthenticationMiddleware, backend=BasicAuthBackend()),
    Middleware(ORMContextMiddleware)
]

app = Starlette(debug=DEBUG, routes=[Route("/", App)], middleware=middleware)
app.mount("/resources/", GraphQLApp(resources_schema, on_get=make_graphiql_handler()))
