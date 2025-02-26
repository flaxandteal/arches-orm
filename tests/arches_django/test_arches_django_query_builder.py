
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

from tests.arches_django.sub_tests.arches_django_query_builder.read.selectors import (
    sub_test_selector_offset, 
    sub_test_selector_first, 
    sub_test_selector_find,
    sub_test_selector_all
)
from tests.arches_django.sub_tests.arches_django_query_builder.read.filters import sub_test_filter_where
from tests.arches_django.sub_tests.arches_django_query_builder.read.modifiers import sub_test_modifier_order_by, sub_test_modifier_lazy

# * Filters
# ! Need to developed or_where aswel, however waiting for where to be completed first
# @context_free
# def test_where_quries_context_free(arches_orm):
#     sub_test_filter_where(arches_orm)

# # * Selectors
# @context_free
# def test_selector_first(arches_orm):
#     sub_test_selector_first(arches_orm)

# @context_free
# def test_selector_find(arches_orm):
#     sub_test_selector_find(arches_orm)

# @context_free
# def test_selector_offset(arches_orm):
#     sub_test_selector_offset(arches_orm)

# @context_free
# def test_all_query_context_free(arches_orm):
#     sub_test_selector_all(arches_orm)

# # * Modifiers
# @context_free
# def test_modifier_lazy(arches_orm):
#     sub_test_modifier_lazy(arches_orm)

# # ! Doesn't work
@context_free
def test_order_by_context_free(arches_orm):
    sub_test_modifier_order_by(arches_orm)