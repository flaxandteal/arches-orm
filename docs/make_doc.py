# Using pdocs for now - if an alternative is required,
# move to sphinx (pdoc/pdoc3 are not options)

import os
import sys
from pathlib import Path
from pdocs.cli import __hug__
from unittest.mock import Mock

OUTPUT_DIR = Path(__file__).parent

def initialize_arches():
    sys.path.append(str(Path(__file__).parent.parent / "tests"))
    os.environ["DJANGO_SETTINGS_MODULE"] = "_django.settings"
    from _django import settings
    settings.WELL_KNOWN_RESOURCE_MODELS = {}

    # Setup Django
    import django
    django.setup()

    sys.modules["arches.app.search.search_engine_factory"] = Mock()

    from django.test.utils import setup_databases
    from pytest_django.fixtures import _disable_migrations
    _disable_migrations()
    setup_databases(verbosity=False, interactive=False)

    from django.db import connection
    with (Path(__file__).parent.parent / "tests" / "_django" / "test.sql").open("r") as sql_f:
        with connection.cursor() as c:
            c.executescript(sql_f.read())

if __name__ == "__main__":
    initialize_arches()
    __hug__.cli()
