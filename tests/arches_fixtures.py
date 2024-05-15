import pytest
from arches_orm.adapter import context_free, get_adapter

@pytest.fixture
@context_free
def person_ash(arches_orm):
    Person = arches_orm.models.Person
    person = Person.create()
    ash = person.name.append()
    ash.full_name = "Ash"
    return person

@pytest.fixture
@context_free
def person_ashs(arches_orm, person_ash):
    person_ash.save()
    yield person_ash
    person_ash.delete()

