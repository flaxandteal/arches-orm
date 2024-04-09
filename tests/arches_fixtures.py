import pytest

@pytest.fixture
def person_ash(arches_orm):
    Person = arches_orm.models.Person
    person = Person.create()
    ash = person.name.append()
    ash.full_name = "Ash"
    return person

@pytest.fixture
def person_ashs(arches_orm, person_ash):
    person_ash.save()
    yield person_ash
    person_ash.delete()

