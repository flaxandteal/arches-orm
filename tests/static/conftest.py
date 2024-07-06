from pathlib import Path

from arches_orm.adapter import get_adapter

get_adapter("static").config.update({
    "concept_paths": [
        Path(__file__).parent.parent / "arches_django" / "_django"
    ],
    "arches_url": "http://arches:8000/"
})
