import pytest
import json

JSON_PERSON = """
{
    "Name": [
        {
            "Forenames": {
                "Forename  Name Type": {
                    "Forename Metatype": "",
                    "@value": ""
                },
                "Forename": null
            },
            "Name Use Type": {
                "Name Use Metatype": "",
                "@value": ""
            },
            "Full Name": "Ash",
            "Titles": {
                "Title Name Type": {
                    "Title Name Metatype": "",
                    "@value": ""
                },
                "Title": ""
            },
            "Full Name Type": {
                "Full Name Metatype": "",
                "@value": ""
            },
            "Surnames": {
                "Surname Name Type": {
                    "Surname Name Metatype": "",
                    "@value": ""
                },
                "Surname": null
            },
            "Initials": {
                "Initial(s) Name Type": {
                    "Initial(s) Name Metatype": "",
                    "@value": ""
                },
                "Initial(s)": null
            },
            "Epithets": {
                "Epithet Name Type": {
                    "Epithet Name Metatype": "",
                    "@value": ""
                },
                "Epithet": null
            }
        }
    ]
}
"""


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

@pytest.mark.django_db
def test_startup(arches_orm):
    Person = arches_orm.models.Person
    person = Person.create()
    ash = person.name.append()
    ash.full_name = "Ash"
    person.save()

@pytest.mark.django_db
def test_unsaved_json(person_ash):
    resource = person_ash.to_resource()
    assert resource.to_json() == json.loads(JSON_PERSON)

@pytest.mark.django_db
def test_find(arches_orm, person_ashs):
    reloaded_person = arches_orm.models.Person.find(person_ashs.id)
    assert reloaded_person.name[0].full_name == "Ash"

@pytest.mark.django_db
def test_empty_node_is_falsy(arches_orm, person_ashs):
    assert not person_ashs.user_account

@pytest.mark.django_db
def test_user_account(arches_orm, person_ashs):
    from django.contrib.auth.models import User
    user_account = User(email="ash@example.com")
    user_account.save()
    person_ashs.user_account = user_account
    assert person_ashs.user_account.email == "ash@example.com"

    person_ashs.save()

    reloaded_person = arches_orm.models.Person.find(person_ashs.id)
    assert reloaded_person.user_account.email == "ash@example.com"

@pytest.mark.django_db
def test_hooks_setup(arches_orm):
    hooks = arches_orm.add_hooks()
    assert hooks == {"post_save", "post_delete"}

@pytest.mark.django_db
def test_can_create_create_by_class_name(arches_orm):
    from arches_orm.utils import get_well_known_resource_model_by_class_name
    Person = get_well_known_resource_model_by_class_name("Person")
    assert Person == arches_orm.models.Person

@pytest.mark.django_db
def test_can_retrieve_by_resource_id(arches_orm, person_ashs):
    from arches_orm.utils import attempt_well_known_resource_model
    person = attempt_well_known_resource_model(person_ashs.id)
    assert person.__eq__(person_ashs)
