import pytest
import json
from uuid import UUID
from arches_orm.adapter import context_free, get_adapter
from arches_orm.utils import string_to_enum
from arches_orm.errors import DescriptorsNotYetSet
from django.db import connection
from tests.utilities.asserts.datatypes import assert_datatype_semmantic
from arches.app.utils.betterJSONSerializer import JSONDeserializer
from pathlib import Path
from arches_orm.view_models import SemanticViewModel, NodeListViewModel, StringViewModel
from tests.utilities.common import create_tile_from_model

from tests.arches_django.sub_tests.queries.read.selectors import all_check_default
from sub_tests.queries.read.filters import sub_test_where_equal, sub_test_or_where_equal
from tests.arches_django.sub_tests.queries.read.modifiers import sub_test_order_by_ascend

def arches_import_method():
    from arches.app.utils.data_management.resources.importer import BusinessDataImporter
    from django.test.utils import captured_stdout
    
    with captured_stdout():
        BusinessDataImporter(
            "tests/arches_django/seed/default/cars/business-data.json"
        ).import_business_data()


# @context_free
# def test_all_query_context_free(arches_orm):
#     Person = arches_orm.models.Person;
#     all_check_default(arches_orm)
#     results = Person.where('full_name=UP')

#     for result in results:
#         print('HERE IS THE VALUE : ',  result.name[0].full_name)

# @context_free
# def test_where_quries_context_free(arches_orm):
#     sub_test_where_equal(arches_orm)

@context_free
def test_all_query_context_free(arches_orm):
    Person = arches_orm.models.Person;
    all_check_default(arches_orm)