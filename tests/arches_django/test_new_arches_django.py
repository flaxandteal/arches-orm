from arches_orm.adapter import context_free

from tests.arches_django.sub_tests.create import (
    sub_test_create,
)

# * Modifiers
@context_free
def test_create(arches_orm):
    sub_test_create(arches_orm)