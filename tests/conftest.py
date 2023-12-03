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

os.environ["DJANGO_SETTINGS_MODULE"] = "_django.settings"
django.setup()

import pytest_django as _
from django.db import connection


@pytest.fixture(scope="session")
def django_db_use_migrations():
    return False


sys.modules["arches.app.search.search_engine_factory"] = Mock()


@pytest.yield_fixture(scope="function")
def arches_orm(django_db_blocker):
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

    from arches.app.utils.betterJSONSerializer import JSONSerializer, JSONDeserializer
    from arches.app.utils.data_management.resource_graphs.importer import (
        import_graph as ResourceGraphImporter,
    )

    with django_db_blocker.unblock() as _:
        from arches.db import dml
    with django_db_blocker.unblock():
        with (Path(__file__).parent / "_django" / "test.sql").open("r") as sql_f:
            with connection.cursor() as c:
                c.executescript(sql_f.read())
    with django_db_blocker.unblock():
        for model in ("Activity.json", "Person.json"):
            with (Path(__file__).parent / "_django" / model).open("r") as f:
                archesfile = JSONDeserializer().deserialize(f)
                errs, importer = ResourceGraphImporter(archesfile["graph"], True)
        import arches_orm

        yield arches_orm

    del sys.modules["arches.app.search.search_engine_factory"]
