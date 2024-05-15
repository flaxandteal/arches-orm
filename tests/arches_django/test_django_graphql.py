import pytest
import os
from httpx import AsyncClient
from graphql import print_schema
import arches_graphql_client
import arches_orm.graphql.auth
from unittest.mock import MagicMock, patch

import pytest_asyncio
from django.contrib.auth.models import User


def nope(*args, **kwargs):
    return False

def yep(*args, **kwargs):
    return True

@pytest.fixture
def agc():
    arches_graphql_client.config._CONFIGURATION["server"]
    return

@pytest.fixture
def anon_app(arches_orm):
    from arches_orm.graphql._asgi import app
    from arches_orm.graphql import auth
    auth.ALLOW_ANONYMOUS = True
    return app


@pytest_asyncio.fixture
async def client(anon_app):
    async with AsyncClient(app=anon_app, base_url="http://testserver") as client:
        yield client

@pytest.fixture
def resource_client(anon_app):
    from arches_graphql_client.resource import ResourceClient
    from gql.transport.httpx import HTTPXAsyncTransport
    from gql import Client
    transport = HTTPXAsyncTransport(
        url="http://testserver/resources/",
        app=anon_app,
        headers={'Authorization': 'basic abc123'}
    )

    resource_client = ResourceClient()
    resource_client.client = Client(transport=transport, fetch_schema_from_transport=True, execute_timeout=10)

    authenticator = arches_orm.graphql.auth.authenticator
    arches_orm.graphql.auth.authenticator = MagicMock()
    OauthlibRequest = arches_orm.graphql.auth.OauthlibRequest
    arches_orm.graphql.auth.OauthlibRequest = MagicMock()
    arches_orm.graphql.auth.authenticator.return_value = True
    admin = User(username="admin", is_superuser=True)
    arches_orm.graphql.auth.OauthlibRequest().client.user = admin
    admin.save()

    def _resource_client(model_name):
        resource_client.resource_model_name = model_name
        return resource_client
    yield _resource_client
    arches_orm.graphql.auth.authenticator = authenticator
    arches_orm.graphql.auth.OauthlibRequest = OauthlibRequest

@pytest.fixture
def unprivileged_resource_client(resource_client):
    user = User(username="rimmer", is_superuser=False)
    arches_orm.graphql.auth.OauthlibRequest().client.user = user
    user.save()
    with (
        patch("arches_orm.arches_django.wrapper.user_can_read_resource", nope) as _,
        patch("arches_orm.arches_django.wrapper.user_can_edit_resource", nope) as _,
        patch("arches_orm.arches_django.wrapper.user_can_read_graph", nope) as __
    ):
        yield resource_client

@pytest.mark.asyncio
async def test_app(client):
    response = await client.get('/')
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_person_schema(anon_app, resource_client, person_ashs):
    person_client = resource_client("Person")
    async with person_client.client as _:
        assert person_client.client.schema
        schema = print_schema(person_client.client.schema)
    assert "PersonName" in schema

@pytest.mark.asyncio
async def test_person_query(anon_app, resource_client, person_ashs):
    person_client = resource_client("Person")
    response = await person_client.get(str(person_ashs.id), ["id"])
    assert response == {"getPerson": {"id": str(person_ashs.id)}}

@pytest.mark.asyncio
async def test_unknown_person_query_gives_none(anon_app, resource_client, person_ashs):
    person_client = resource_client("Person")
    response = await person_client.get("5a27548e-394b-4371-b224-e93ce68e9768", ["id"])
    assert response == {"getPerson": None}

@pytest.mark.asyncio
async def test_person_properties(anon_app, resource_client, person_ashs):
    person_client = resource_client("Person")
    response = await person_client.get(str(person_ashs.id), ["id", ("name", ["fullName"])])
    assert response == {"getPerson": {"id": str(person_ashs.id), "name": [{"fullName": "Ash"}]}}

@pytest.mark.asyncio
async def test_person_create(anon_app, resource_client, person_ash):
    person_client = resource_client("Person")
    response = await person_client.create({
        "name": [{"fullName": "Ash"}]
    })
    new_id = response["id"]
    response = await person_client.get(new_id, ["id", ("name", ["fullName"])])
    assert response == {"getPerson": {"id": new_id, "name": [{"fullName": "Ash"}]}}

@pytest.mark.asyncio
@pytest.mark.parametrize("debug", [False, True])
@pytest.mark.parametrize("graph", [False, True])
@pytest.mark.parametrize("can_edit", [False, True])
async def test_person_query_fails_if_unprivileged(anon_app, unprivileged_resource_client, person_ashs, debug, graph, can_edit):
    with patch("arches_orm.graphql.resources.GRAPHQL_DEBUG_PERMISSIONS", debug) as _:
        person_client = unprivileged_resource_client("Person")
        with (
            patch("arches_orm.arches_django.wrapper.user_can_read_graph", yep if graph else nope) as _
        ):
            response = await person_client.get(str(person_ashs.id), ["id"])
            assert response == {"getPerson": {"id": f"{'Instance' if graph else 'Model'} permission denied"} if debug else None}

            # We cannot give permission errors to unknown UUIDs, as they could be any model.
            # TODO: throw error if a resource client isn't finding the expected model.
            response = await person_client.get("5a27548e-394b-4371-b224-e93ce68e9768", ["id"])
            assert response == {"getPerson": None}

            with (
                patch("arches_orm.arches_django.wrapper.user_can_edit_resource", yep if can_edit else nope) as _
            ):
                response = await person_client.create({
                    "name": [{"fullName": "Ash"}]
                })
            if not can_edit or not graph:
                assert response is None
            else:
                assert response.get("id") is not None
