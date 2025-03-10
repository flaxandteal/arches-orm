from arches_orm.adapter import context_free

from tests.arches_django.sub_tests.arches_django_query_builder.selectors import (
    sub_test_selector_offset, 
    sub_test_selector_first, 
    sub_test_selector_find,
    sub_test_selector_all
)
from tests.arches_django.sub_tests.arches_django_query_builder.filters import sub_test_filter_where
from tests.arches_django.sub_tests.arches_django_query_builder.modifiers import sub_test_modifier_order_by, sub_test_modifier_lazy

# # * Modifiers
# @context_free
# def test_modifier_lazy(arches_orm):
#     sub_test_modifier_lazy(arches_orm)
    
# @context_free
# def test_selector_offset(arches_orm):
#     sub_test_selector_offset(arches_orm)

# # * Selectors
# @context_free
# def test_selector_first(arches_orm):
#     sub_test_selector_first(arches_orm)

# # * Filters
# # ! Need to developed or_where aswel, however waiting for where to be completed first
# @context_free
# def test_where_quries_context_free(arches_orm):
#     sub_test_filter_where(arches_orm)

# @context_free
# def test_selector_find(arches_orm):
#     sub_test_selector_find(arches_orm)

# @context_free
# def test_all_query_context_free(arches_orm):
#     sub_test_selector_all(arches_orm)

# ? https://huly.galviadigital.com/workbench/galviadigital/tracker/EMR-106
@context_free
def test_order_by_context_free(arches_orm):
    sub_test_modifier_order_by(arches_orm)