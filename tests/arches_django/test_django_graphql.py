import pytest
import os
from httpx import AsyncClient
from graphql import print_schema
import arches_graphql_client
import arches_orm.graphql.auth
from unittest.mock import MagicMock, patch

import pytest_asyncio
from django.contrib.auth.models import User


RECORD_STATUS = "7849cd3c-3f0d-454d-aaea-db9164629641"


def nope(*args, **kwargs):
    return False

def yep(*args, **kwargs):
    return True

@pytest.fixture
def agc():
    arches_graphql_client.config._CONFIGURATION["server"]
    return

@pytest.fixture
def app(arches_orm):
    from arches_orm.graphql._asgi import app
    return app


@pytest_asyncio.fixture
async def client(app):
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        yield client

@pytest.fixture
def concept_client(app):
    from arches_graphql_client.concept import ConceptClient
    concept_client = ConceptClient()
    yield from client_builder(app, "concepts/", concept_client)

@pytest.fixture
def resource_client(app):
    from arches_graphql_client.resource import ResourceClient
    resource_client = ResourceClient()
    def _resource_client(model_name):
        resource_client.resource_model_name = model_name
        return resource_client
    yield from client_builder(app, "resources/", resource_client, _resource_client)

def client_builder(app, path, client, wrapper=None):
    from gql.transport.httpx import HTTPXAsyncTransport
    from gql import Client
    transport = HTTPXAsyncTransport(
        url=f"http://testserver/{path}",
        app=app,
        headers={'Authorization': 'basic abc123'}
    )

    client.client = Client(transport=transport, fetch_schema_from_transport=True, execute_timeout=10)

    authenticator = arches_orm.graphql.auth.authenticator
    arches_orm.graphql.auth.authenticator = MagicMock()
    OauthlibRequest = arches_orm.graphql.auth.OauthlibRequest
    arches_orm.graphql.auth.OauthlibRequest = MagicMock()
    arches_orm.graphql.auth.authenticator.return_value = True
    admin = User(username="admin", is_superuser=True)
    arches_orm.graphql.auth.OauthlibRequest().client.user = admin
    admin.save()

    yield wrapper or client
    arches_orm.graphql.auth.authenticator = authenticator
    arches_orm.graphql.auth.OauthlibRequest = OauthlibRequest

def deprivilege_client(client):
    user = User(username="rimmer", is_superuser=False)
    arches_orm.graphql.auth.OauthlibRequest().client.user = user
    user.save()
    with (
        patch("arches_orm.arches_django.wrapper.user_can_read_resource", nope) as _,
        patch("arches_orm.arches_django.wrapper.user_can_edit_resource", nope) as _,
        patch("arches_orm.arches_django.wrapper.user_can_read_graph", nope) as __
    ):
        yield client

@pytest.fixture
def unprivileged_concept_client(concept_client):
    yield from deprivilege_client(concept_client)

@pytest.fixture
def unprivileged_resource_client(resource_client):
    yield from deprivilege_client(resource_client)

@pytest.mark.asyncio
async def test_app(client):
    response = await client.get('/')
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_person_schema(app, resource_client, person_ashs):
    person_client = resource_client("Person")
    async with person_client.client as _:
        assert person_client.client.schema
        schema = print_schema(person_client.client.schema)
    assert "PersonName" in schema

@pytest.mark.asyncio
async def test_person_query(app, resource_client, person_ashs):
    person_client = resource_client("Person")
    response = await person_client.get(str(person_ashs.id), ["id"])
    assert response == {"getPerson": {"id": str(person_ashs.id)}}

@pytest.mark.asyncio
async def test_unknown_person_query_gives_none(app, resource_client, person_ashs):
    person_client = resource_client("Person")
    response = await person_client.get("5a27548e-394b-4371-b224-e93ce68e9768", ["id"])
    assert response == {"getPerson": None}

@pytest.mark.asyncio
async def test_person_properties(app, resource_client, person_ashs):
    person_client = resource_client("Person")
    response = await person_client.get(str(person_ashs.id), ["id", ("name", ["fullName"])])
    assert response == {"getPerson": {"id": str(person_ashs.id), "name": [{"fullName": "Ash"}]}}

@pytest.mark.asyncio
async def test_concept_get_only_if_privileged(app, unprivileged_concept_client):
    from gql.transport.exceptions import TransportQueryError
    with pytest.raises(TransportQueryError):
        await unprivileged_concept_client.get_concept(RECORD_STATUS)

@pytest.mark.asyncio
async def test_concept_get_by_id(app, concept_client):
    concept = await concept_client.get_concept(RECORD_STATUS)
    assert concept == {
        "id": RECORD_STATUS,
        "label": "Record Status",
        "slug": "RecordStatus",
        "nodetype": "Collection"
    }

@pytest.mark.asyncio
async def test_concept_get_terms(app, concept_client):
    terms = await concept_client.get_terms("RecordStatus")
    TERMS = [
        {
            'label': 'Active - Full/Published',
            'slug': 'ActiveDashFullOrPublished',
            'fullLabel': ['Active - Full/Published'],
        },
        {
            'label': 'Backlog - Full/Published',
            'slug': 'BacklogDashFullOrPublished',
            'fullLabel': ['Backlog - Full/Published'],
        },
        {
            'label': 'Backlog - Skeleton',
            'slug': 'BacklogDashSkeleton',
            'fullLabel': ['Backlog - Skeleton'],
        }
    ]
    term_map = {term["slug"]: term for term in TERMS}
    comparison = []
    for term in terms:
        term_map[term["slug"]]["identifier"] = term["identifier"]
        comparison.append(term_map[term["slug"]])

    assert terms == comparison

@pytest.mark.asyncio
async def test_concept_add_term(app, concept_client):
    concept_ok = await concept_client.add_term("RecordStatus", "RecordStatus》New Status")
    assert concept_ok == {"ok": True}
    terms = await concept_client.get_term_list("RecordStatus")
    assert "NewStatus" in terms

@pytest.mark.asyncio
async def test_concept_get_by_name(app, concept_client):
    concept = await concept_client.get_concept("RecordStatus")
    assert concept == {
        "id": RECORD_STATUS,
        "label": "Record Status",
        "slug": "RecordStatus",
        "nodetype": "Collection"
    }

@pytest.mark.asyncio
async def test_person_create(app, resource_client, person_ash):
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
async def test_person_query_fails_if_unprivileged(app, unprivileged_resource_client, person_ashs, debug, graph, can_edit):
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
