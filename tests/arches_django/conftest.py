import os
import sys
import pytest
from pathlib import Path
from unittest.mock import Mock
import uuid
from django.db.models import fields
from django.db.transaction import atomic, rollback, savepoint, savepoint_commit, savepoint_rollback
import sqlite3

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

import django # noqa: E402

os.environ.update({
    "DJANGO_MODE": "TEST",
    "DJANGO_DEBUG": "False",
    "PGDBNAME": "",
    "PGUSERNAME": "",
    "PGPASSWORD": "",
    "PGHOST": "",
    "PGPORT": "",
    "ESPORT": "",
    "ESHOST": "",
    "DOMAIN_NAMES": "",
})
if os.environ.get("WITH_GRAPHQL", True):
    os.environ["DJANGO_SETTINGS_MODULE"] = "_django.settings_graphql"
else:
    os.environ["DJANGO_SETTINGS_MODULE"] = "_django.settings"
os.environ["DJANGO_MODE"] = "DEV"
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
os.environ.update({
    "INSTALL_DEFAULT_GRAPHS": "True",
    "INSTALL_DEFAULT_CONCEPTS": "True",
    "PGUSERNAME": "postgres",
    "PGPASSWORD": "postgres",
    "PGDBNAME": "arches2",
    "PGHOST": "sut_db",
    "PGPORT": "5432",
    "ESHOST": "sut_es",
    "ESPORT": "9200",
    "DJANGO_MODE": "PROD",
    "DJANGO_DEBUG": "False",
    "DOMAIN_NAMES": "localhost",
    "PYTHONUNBUFFERED": "0",
    "TZ": "PST",
})
django.setup()

from django.db import connection # noqa: E402


@pytest.fixture(scope="session")
def django_db_use_migrations():
    return False


@pytest.fixture(scope="session")
def search_engine():
    sef = Mock()
    sys.modules["arches.app.search.search_engine_factory"] = sef
    search_results = {"hits": {"hits": []}}
    sef.SearchEngineInstance.search = lambda *args, **kwargs: search_results
    sys.modules["arches.app.search.search_engine_factory"] = sef
    yield
    del sys.modules["arches.app.search.search_engine_factory"]

@pytest.fixture(scope="session")
def test_sql(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        with (Path(__file__).parent / "_django" / "test.sql").open("r") as sql_f:
            with connection.cursor() as c:
                c.executescript(sql_f.read())
    yield


@pytest.fixture(scope="session")
def arches_orm_(search_engine, django_db_blocker, test_sql):
    # Sqlite cannot handle JSON-contains filtering, or jsonb_set
    from arches.app.models import tile
    from arches.app.models.fields import i18n
    from arches.app.utils.skos import SKOSReader

    tile.Tile._getFunctionClassInstances = lambda _: []
    I18n_String_orig = i18n.I18n_String.as_sql

    # * SQLite does not support JSONB functions like jsonb_set, which are used in PostgreSQL.
    # * The fixture modifies methods in the arches ORM to replace these with SQLite-compatible versions.
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

    # Disabling Post Tile Save Function
    # No functions in Sqlite
    ResourceInstanceDataType.post_tile_save = lambda *args, **kwargs: ()
    from arches.app.models.concept import Concept
    def _get_child_collections(_, conceptid, child_valuetypes=None, parent_valuetype="prefLabel", columns=None, depth_limit=None):
        child_valuetypes = child_valuetypes if child_valuetypes else ["prefLabel"]
        if columns is None:
            columns = "r.conceptidto, valueto.value as valueto, valueto.valueid as valueidto"
        # Ignores children!
        sql = f"""
        SELECT {columns}
            FROM relations r
            JOIN "values" valueto ON r.conceptidto=valueto.conceptid
            JOIN "values" valuefrom ON(r.conceptidfrom = valuefrom.conceptid)
            WHERE r.conceptidfrom = %(conceptid)s AND r.relationtype = 'member'
            AND valueto.valuetype in (%(child_valuetypes)s)
            AND valuefrom.valuetype in (%(child_valuetypes)s)
        """
        cursor = connection.cursor()
        cursor.execute(
            sql,
            {
                "conceptid": conceptid,
                "child_valuetypes": "', '".join(child_valuetypes)
            }
        )
        return cursor.fetchall()

    def _get_child_collections_hierarchically(_, conceptid, child_valuetypes=None, offset=0, limit=50, query=None):
        # Ignores children!
        columns = "valueto.value as valueto, valueto.valueid as valueidto, r.conceptidto, NULL as language, valueto.valuetype as valuetype, 1 as depth, NULL as collector, count(*) AS full_count"
        collections = _get_child_collections(_, conceptid, child_valuetypes=child_valuetypes, columns=columns)
        unflattened = []
        for collection in collections:
            unflattened.append([
                {
                    "value": collection[0],
                    "valueid": collection[1],
                    "conceptid": collection[2],
                    "language": collection[3],
                    "valuetype": collection[4],
                },
                *collection[2:5]
            ])
        return unflattened

    Concept.get_child_collections = _get_child_collections
    Concept.get_child_collections_hierarchically = _get_child_collections_hierarchically

    from django.contrib.auth.models import User
    from arches.app.utils.betterJSONSerializer import JSONDeserializer
    from arches.app.utils.data_management.resource_graphs.importer import (
        import_graph as ResourceGraphImporter,
    )
    from arches.app.utils.data_management.resources.importer import (
        import_one_resource,
    )
    from arches.app.models.models import PublishedGraph
    import uuid

    with django_db_blocker.unblock():
        skos = SKOSReader()
        for rdf_file in ("collections.xml", "Record_Status.xml", "Nismr_Numbering.xml"):
            rdf = skos.read_file(str(Path(__file__).parent / "_django" / rdf_file))
            skos.save_concepts_from_skos(rdf, "overwrite", "keep", prevent_indexing=True)

        # ! Method doesn't use RDF files, need to update this, however runnnig into too many problems so will make a ticket on this
        # ! https://huly.galviadigital.com/workbench/galviadigital/tracker/EMR-48
        def _seed_database(seed_type: str = 'default'):
            """
            Handles the seeding of the database and uses the data inside seed/${seed_type}/...

            @param seed_type: The seeder type so default or maybe only a certain user
            """
            directory = Path(__file__).parent / "seed" / seed_type

            # def _handle_rdf_seed(parent_folder:    str):
            #     for file in (directory / parent_folder).iterdir():
            #         print(directory / parent_folder / file.name)
            #         rdf = skos.read_file(directory / parent_folder / file.name)
            #         skos.save_concepts_from_skos(rdf, "overwrite", "keep", prevent_indexing=True)

            # _handle_rdf_seed('rdf')

            def _handle_models(parent_folder):
                """
                Method handles the seeding of models from a JSON

                @param parent_folder: This is the parent_folder of where the graph.json should be located
                """
                if not (directory / parent_folder.name / 'graph.json').exists():
                    return;
            
                with (directory / parent_folder.name / 'graph.json').open("r") as f:
                    archesfile = JSONDeserializer().deserialize(f)

                    print(parent_folder.name)

                    # ! This has to be defined or errors are given
                    # archesfile["graph"]["cards_x_nodes_x_widgets"] = []
                    ResourceGraphImporter(archesfile["graph"], True)

                    _handle_business_data(parent_folder)

            def _handle_business_data(parent_folder, **updates):
                import json
                from arches.app.utils.data_management.resources.importer import BusinessDataImporter

                if not (directory / parent_folder.name / 'business-data.json').exists():
                    return;
            

                # # Instantiate the BusinessDataImporter
                # business_data_importer = BusinessDataImporter(
                #     file=directory / parent_folder.name / 'business-data.json',
                # )

                # # Now call the import method with any necessary arguments
                # business_data_importer.import_business_data(
                #     file_format="json",  # Specify the format of your data file
                #     overwrite="overwrite",  # Can be "append" or "overwrite"
                #     bulk=False,  # For bulk importing, set this to True
                #     create_concepts=True,  # Set whether to create new concepts
                #     create_collections=True,  # Set whether to create new collections
                #     use_multiprocessing=False,  # Enable multiprocessing if needed
                #     prevent_indexing=False  # Prevent indexing if required
                # )
            
                with (directory / parent_folder.name / 'business-data.json').open("r") as f:
                    archesfile = JSONDeserializer().deserialize(f)

                    for resource in archesfile['business_data']['resources']:
                        if ('graph_publication_id' in updates):
                            resource['resourceinstance']['graph_publication_id'] = updates['graph_publication_id']

                        if ('publication_id' in updates):
                            resource['resourceinstance']['publication_id'] = updates['publication_id']

                        import_one_resource(json.dumps(resource))

                 
                    

            for parent_folder in directory.iterdir():
                if (parent_folder.name == 'rdf'):
                    # _handle_rdf_seed(parent_folder)
                    continue

                else:
                    _handle_models(parent_folder)


        
        from arches_orm.adapter import ADAPTER_MANAGER
        ADAPTER_MANAGER.set_default_adapter("arches-django")

        admin = User(username="admin", is_superuser=True)
        admin.save()
        user = User(username="rimmer", is_superuser=False)
        user.save()

        import arches_orm.arches_django
        from arches_orm.adapter import get_adapter
        get_adapter("arches-django").config["save_crosses"] = True
        import arches_orm.models
        def printTables():
            with connection.cursor() as cursor:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()

            print(tables)  # This will show all tables in the database
        printTables()
        
        _seed_database()
        
        # Assuming this file is in arches/app/models/migrations/7125_geometry_index_table.py

    # # Create a custom function that simulates the refresh_geojson_geometries behavior
    #     def refresh_geojson_geometries_fake(*args):
    #         print("refresh_geojson_geometries was called")
    #         return True

    #     # Connect to your SQLite database
    #     with connection.cursor() as cursor:
    #         # Register the fake function with SQLite
    #         connection.create_function("refresh_geojson_geometries", 0, refresh_geojson_geometries_fake)

    #         # Now, you can execute the function within a query context via the cursor
    #         cursor.execute("SELECT refresh_geojson_geometries();")
    #         result = cursor.fetchone()
    #         print(result)


        yield arches_orm



@pytest.fixture(scope="function")
def arches_orm(django_db_serialized_rollback, arches_orm_, search_engine):
    with atomic():
        yield arches_orm_
