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
def test_can_save_with_name(arches_orm):
    Person = arches_orm.models.Person
    person = Person.create()
    ash = person.name.append()
    ash.full_name = "Ash"
    person.save()

@pytest.mark.django_db
def test_can_save_with_blank_name(arches_orm):
    Person = arches_orm.models.Person
    person = Person.create()
    person.name.append()
    person.save()

@pytest.mark.django_db
def test_can_save_two_names(arches_orm, person_ashs):
    asha = person_ashs.name.append()
    asha.full_name = "Asha"
    assert len(person_ashs.name) == 2
    person_ashs.save()
    assert len(person_ashs.name) == 2

    reloaded_person = arches_orm.models.Person.find(person_ashs.id)
    assert len(reloaded_person.name) == 2
    full_names = {name.full_name for name in reloaded_person.name}
    assert full_names == {"Ash", "Asha"}

@pytest.mark.django_db
def test_can_save_two_related_resources(arches_orm, person_ashs):
    act_1 = arches_orm.models.Activity()
    person_ashs.associated_activities.append(act_1)
    person_ashs.save()
    assert len(person_ashs.associated_activities) == 1

    reloaded_person = arches_orm.models.Person.find(person_ashs.id)
    assert len(reloaded_person.name) == 1
    act_2 = arches_orm.models.Activity()
    reloaded_person.associated_activities.append(act_2)
    reloaded_person.save()
    assert len(reloaded_person.associated_activities) == 2

    reloaded_person = arches_orm.models.Person.find(person_ashs.id)
    assert len(reloaded_person.associated_activities) == 2

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

@pytest.mark.django_db
def test_can_attach_related(arches_orm, person_ashs):
    activity = arches_orm.models.Activity()
    person_ashs.associated_activities.append(activity)
    assert len(person_ashs.associated_activities) == 1

@pytest.mark.django_db
def test_can_attach_related_then_save(arches_orm, person_ashs):
    activity = arches_orm.models.Activity()
    person_ashs.associated_activities.append(activity)
    assert len(person_ashs.associated_activities) == 1
    person_ashs.save()
    assert len(person_ashs.associated_activities) == 1
    reloaded_person = arches_orm.models.Person.find(person_ashs.id)
    assert len(reloaded_person.associated_activities) == 1
    assert isinstance(reloaded_person.associated_activities[0], arches_orm.models.Activity)
