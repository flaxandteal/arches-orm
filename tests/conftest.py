import spatialite
import os
import sys
import pytest
from pathlib import Path
from unittest.mock import Mock
import uuid
from django.db.models import fields


# Workaround for Sqlite being given string UUIDs
def _get_db_prep_value(self, value, connection, prepared=False):
    # Taken from Django DB
    if value is None:
        return None
    if not isinstance(value, uuid.UUID):
        value = self.to_python(value)

    if connection.features.has_native_uuid_field:
        return value
    return str(value)  # This is the critical change, from value.hex


fields.UUIDField.get_db_prep_value = _get_db_prep_value

import django
from django.core.management import call_command

if os.environ.get("WITH_GRAPHQL", True):
    os.environ["DJANGO_SETTINGS_MODULE"] = "_django.settings_graphql"
else:
    os.environ["DJANGO_SETTINGS_MODULE"] = "_django.settings"
django.setup()

import pytest_django as _
from django.db import connection


@pytest.fixture(scope="session")
def django_db_use_migrations():
    return False


@pytest.fixture(scope="function")
def search_engine():
    sef = Mock()
    sys.modules["arches.app.search.search_engine_factory"] = sef
    se = Mock()
    search_results = {"hits": {"hits": []}}
    sef.SearchEngineInstance.search = lambda *args, **kwargs: search_results
    sys.modules["arches.app.search.search_engine_factory"] = sef
    yield
    del sys.modules["arches.app.search.search_engine_factory"]

@pytest.fixture(scope="function")
def test_sql(transactional_db, django_db_blocker):
    with django_db_blocker.unblock():
        with (Path(__file__).parent / "_django" / "test.sql").open("r") as sql_f:
            with connection.cursor() as c:
                c.executescript(sql_f.read())
            yield


@pytest.fixture(scope="function")
def arches_orm(search_engine, django_db_blocker, test_sql):
    # Sqlite cannot handle JSON-contains filtering, or jsonb_set
    from arches.app.models import tile
    from arches.app.models.fields import i18n

    tile.Tile._getFunctionClassInstances = lambda _: []
    I18n_String_orig = i18n.I18n_String.as_sql

    def I18n_String_sql(s, c, c_):
        sql, params = I18n_String_orig(s, c, c_)
        return sql.replace("jsonb_set", "json_set"), params

    i18n.I18n_String.as_sql = I18n_String_sql
    I18n_JSON_orig = i18n.I18n_JSON.as_sql

    def I18n_JSON_sql(s, c, c_):
        sql, params = I18n_JSON_orig(s, c, c_)
        return sql.replace("jsonb_set", "json_set"), params

    i18n.I18n_JSON.as_sql = I18n_JSON_sql

    from arches.app.datatypes.datatypes import ResourceInstanceDataType
    # No functions in Sqlite
    ResourceInstanceDataType.post_tile_save = lambda *args, **kwargs: ()
    from arches.app.models.concept import Concept
    Concept.get_child_collections = lambda *args, **kwargs: [
        (None, "First", "Value1"),
        (None, "Second", "Value2"),
    ]

    from arches.app.utils.betterJSONSerializer import JSONDeserializer
    from arches.app.utils.data_management.resource_graphs.importer import (
        import_graph as ResourceGraphImporter,
    )

    with django_db_blocker.unblock():
        for model in ("Activity.json", "Person.json"):
            with (Path(__file__).parent / "_django" / model).open("r") as f:
                archesfile = JSONDeserializer().deserialize(f)
                ResourceGraphImporter(archesfile["graph"], True)
        import arches_orm.arches_django
        from arches_orm.adapter import get_adapter
        get_adapter("arches-django").config["save_crosses"] = True
        import arches_orm.models

        yield arches_orm
