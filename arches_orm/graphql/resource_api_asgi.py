from pathlib import Path
from arches_orm import resource_api
from arches_orm.adapter import get_adapter

get_adapter("resource_api").config.update({
    "concept_paths": [
        Path(__file__).parent.parent / "arches_django" / "_django"
    ],
    "model_paths": [
        Path(__file__).parent.parent.parent / "tests" / "resource_api" / "_models"
    ],
    "resource_paths": [
        Path(__file__).parent / "_resources"
    ],
    "arches_url": "http://arches:8000/",
    "client": {
        "base_url": "http://hub3.her:3001/",
    }
})

from arches_orm.graphql import _asgi # noqa: E402
app = _asgi.app
