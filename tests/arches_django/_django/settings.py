from django.core.exceptions import ImproperlyConfigured
from arches.settings import * # noqa: F403
from arches.settings import DATATYPE_LOCATIONS

INSTALLED_APPS = (
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "guardian",
    "arches",
    "arches.app.models",
)
FILENAME_GENERATOR = "arches.app.utils.storage_filename_generator.generate_filename"
DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": "arches2",  # You still need to specify a name
        "USER": "postgres",  # Provide user credentials
        "PASSWORD": "postgres",
        "HOST": "localhost",  # Or your PostgreSQL host
        "PORT": "5432",  # Default PostgreSQL port
        "OPTIONS": {
            "options": "-c search_path=pg_temp,public"  # Use temporary schema
        }
    }
}

ELASTICSEARCH_HOSTS = []
ELASTICSEARCH_PREFIX = ""
ELASTICSEARCH_CONNECTION_OPTIONS = {}
WELL_KNOWN_RESOURCE_MODELS = [
    dict(
        model_name="Person",
        graphid="22477f01-1a44-11e9-b0a9-000d3ab1e588",
        user_account={
            "type": "user",
            "lang": "en",
            "nodegroupid": "b1f5c336-6a0e-11ee-b748-0242ac140009",
            "nodeid": "b1f5c336-6a0e-11ee-b748-0242ac140009",
        },
        remapping={"generated_smr": "generated_smr"}
    ),
    dict(
        model_name="Cars",
        graphid="a8947777-c79b-4396-9da9-d1fd5c7a00be",
        user_account={
            "type": "user",
            "lang": "en",
            "nodegroupid": "b1f5c336-6a0e-11ee-b748-0242ac140009",
            "nodeid": "b1f5c336-6a0e-11ee-b748-0242ac140009",
        },
        remapping={"generated_smr": "generated_smr"}
    ),
    dict(
        model_name="Hobbies",
        graphid="916bfb89-f68f-4154-8a54-84bd6f0d3ed3",
        user_account={
            "type": "user",
            "lang": "en",
            "nodegroupid": "b1f5c336-6a0e-11ee-b748-0242ac140009",
            "nodeid": "b1f5c336-6a0e-11ee-b748-0242ac140009",
        },
        remapping={"generated_smr": "generated_smr"}
    ),
    dict(
        model_name="Activity",
        graphid="b9e0701e-5463-11e9-b5f5-000d3ab1e588",
    )
]
MIGRATE = False
DATATYPE_LOCATIONS.append("_django.datatypes")
