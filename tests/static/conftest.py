import pytest
from pathlib import Path

from arches_orm import static as static
from arches_orm.adapter import get_adapter

get_adapter("static").config.update({
    "concept_paths": [
        Path(__file__).parent.parent.parent.parent / "coral-arches" / "coral" / "pkg" / "reference_data" / "concepts",
        Path(__file__).parent.parent.parent.parent / "coral-arches" / "coral" / "pkg" / "reference_data" / "collections"
        # Path(__file__).parent.parent / "arches_django" / "_django"
    ],
    "model_paths": [
        Path(__file__).parent / "_models"
    ],
    "resource_paths": [
        Path(__file__).parent / "_resources"
    ],
    "arches_url": "http://arches:8000/"
})

@pytest.fixture(scope="function")
def arches_orm():
    import arches_orm.models

    yield arches_orm
