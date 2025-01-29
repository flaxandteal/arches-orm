import pytest
from pathlib import Path

from arches_orm.adapter import get_adapter, ADAPTER_MANAGER
from arches_orm import static

@pytest.fixture(scope="function")
def arches_orm():
    import arches_orm
    ADAPTER_MANAGER.set_default_adapter("static")
    yield arches_orm

get_adapter("static").config.update({
    "concept_paths": [
        Path(__file__).parent.parent / "arches_django" / "_django"
    ],
    "arches_url": "http://arches:8000/"
})
