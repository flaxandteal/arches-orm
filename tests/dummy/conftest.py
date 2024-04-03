import os
import sys
import pytest
from pathlib import Path
from unittest.mock import Mock
import uuid

@pytest.fixture(scope="function")
def arches_orm():
    import arches_orm.dummy
    import arches_orm.adapter
    arches_orm.adapter.get_adapter().get_wkrm_definitions().append({
        "model_name": "Person",
        "graphid": 1,
    })
    import arches_orm.wkrm
    import arches_orm.models

    yield arches_orm
