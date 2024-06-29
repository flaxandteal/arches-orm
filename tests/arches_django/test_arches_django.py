import pytest
import json
from arches_orm.adapter import context_free, get_adapter
from arches_orm.errors import DescriptorsNotYetSet

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


@pytest.mark.django_db
@context_free
def test_can_save_with_name(arches_orm):
    Person = arches_orm.models.Person
    person = Person.create()
    ash = person.name.append()
    ash.full_name = "Ash"
    person.save()

@pytest.mark.django_db
@context_free
@pytest.mark.parametrize("lazy", [False, True])
def test_can_save_with_county_value(arches_orm, lazy):
    Person = arches_orm.models.Person
    person = Person.create()
    person.location_data.append().addresses.county.county_value = "Antrim"
    person.save()

    reloaded_person = arches_orm.models.Person.find(person.id, lazy=lazy)
    assert reloaded_person.location_data[0].addresses.county.county_value == "Antrim"

@pytest.mark.django_db
@context_free
@pytest.mark.parametrize("lazy", [False, True])
def test_can_remove_name(arches_orm, lazy):
    Person = arches_orm.models.Person
    person = Person.create()
    person.name.append().full_name = "Asha"
    person.save()
    person.name.pop()
    person.save()
    person.name.append().full_name = "Asha"
    person.save()

    reloaded_person = arches_orm.models.Person.find(person.id, lazy=lazy)
    assert reloaded_person.name[0].full_name == "Asha"

    reloaded_person.name.clear()
    reloaded_person.save()
    reloaded_person = arches_orm.models.Person.find(person.id, lazy=lazy)
    assert len(reloaded_person.name) == 0

    reloaded_person.name.append().full_name = "Asha"
    reloaded_person.save()
    reloaded_person = arches_orm.models.Person.find(person.id, lazy=lazy)
    assert reloaded_person.name[0].full_name == "Asha"

    reloaded_person.name.remove(reloaded_person.name[0])
    reloaded_person.save()
    reloaded_person = arches_orm.models.Person.find(person.id, lazy=lazy)
    assert len(reloaded_person.name) == 0

    reloaded_person.name.append().full_name = "Asha"
    reloaded_person.save()
    reloaded_person = arches_orm.models.Person.find(person.id, lazy=lazy)
    assert reloaded_person.name[0].full_name == "Asha"

    reloaded_person.name.pop(0)
    reloaded_person.save()
    reloaded_person = arches_orm.models.Person.find(person.id, lazy=lazy)
    assert len(reloaded_person.name) == 0

@pytest.mark.django_db
@context_free
@pytest.mark.parametrize("lazy", [False, True])
def test_can_save_with_geojson(arches_orm, lazy):
    Activity = arches_orm.models.Activity
    activity = Activity.create()
    activity.geospatial_coordinates = {
        'geometry': {
            'geospatialCoordinates': {
                'type': 'FeatureCollection',
                'features': [
                    {
                        'id': '1000',
                        'type': 'Feature',
                        'properties': {
                            'Captured_by': 'MC',
                            'Date_Captured': 1259539000000.0
                        },
                        'geometry': {
                            'type': 'Polygon',
                            'coordinates': [
                                [
                                    [-7.0821688272290935, 54.921622989437154],
                                    [-7.082510380464253, 54.92160087302468],
                                    [-7.0825, 54.921],
                                    [-7.0826, 54.921],
                                    [-7.0821, 54.921]
                                ]
                            ]
                        }
                    }
                ]
            }
        }
    }

@pytest.mark.django_db
@context_free
def test_can_get_collection(arches_orm):
    Activity = arches_orm.models.Activity
    activity = Activity.create()
    record_status = activity.record_status_assignment.record_status
    StatusEnum = record_status.__collection__

    assert StatusEnum == get_adapter().get_collection("7849cd3c-3f0d-454d-aaea-db9164629641")

@pytest.mark.django_db
@context_free
@pytest.mark.parametrize("lazy", [False, True])
def test_can_save_with_concept(arches_orm, lazy):
    Activity = arches_orm.models.Activity
    activity = Activity.create()
    record_status = activity.record_status_assignment.record_status
    StatusEnum = record_status.__collection__

    activity.record_status_assignment.record_status = StatusEnum.BacklogDashSkeleton
    assert activity.record_status_assignment.record_status == StatusEnum.BacklogDashSkeleton
    activity.save()

    reloaded_activity = arches_orm.models.Activity.find(activity.id, lazy=lazy)
    assert reloaded_activity.record_status_assignment.record_status == StatusEnum.BacklogDashSkeleton

@pytest.mark.django_db
@context_free
def test_can_get_descriptors(arches_orm):
    Person = arches_orm.models.Person
    person = Person.create()
    name = person.name.append()
    name.full_name = "Ash"
    with pytest.raises(DescriptorsNotYetSet):
        str(person)
    person.save()
    assert str(person) == "Ash"
    assert person._._name == "Ash"
    assert person._._description == "<Description>"
    person.descriptions.append().description = "A person"
    assert person._._description == "<Description>"
    person.save()
    assert person._._description == "A person"
    assert person.describe() == {
        "name": "Ash",
        "description": "A person"
    }

@pytest.mark.django_db
@context_free
def test_can_save_with_blank_name(arches_orm):
    Person = arches_orm.models.Person
    person = Person.create()
    person.name.append()
    person.save()

@pytest.mark.django_db
@context_free
@pytest.mark.parametrize("lazy", [False, True])
def test_can_remap_and_set(arches_orm, lazy):
    Person = arches_orm.models.Person
    person = Person.create()
    remapping = {
        "name": "name*full_name",
        "surname": "name*surnames.surname"
    }
    person._model_remapping = remapping
    person.name.append("Ash")
    person.surname.append("Ash2")
    person.save()
    reloaded_person = arches_orm.models.Person.find(person.id, lazy=lazy)
    assert reloaded_person.name[1].surnames.surname == "Ash2"
    reloaded_person._model_remapping = remapping
    assert reloaded_person.name == ["Ash", None]
    assert reloaded_person.surname == [None, "Ash2"]

@pytest.mark.django_db
@context_free
def test_can_remap_loaded(arches_orm, person_ashs):
    person_ashs._model_remapping = {"name": "name*full_name"}
    assert person_ashs.name == ["Ash"]

@pytest.mark.django_db
@context_free
def test_can_remap_and_set_loaded(arches_orm, person_ashs):
    person_ashs._model_remapping = {"name": "name.full_name"}
    person_ashs.name = "Noash"
    assert person_ashs.name == "Noash"

    person_ashs._model_remapping = {"name": "name*full_name"}
    person_ashs.name = "Noash"
    assert person_ashs.name == ["Noash"]

@pytest.mark.django_db
@context_free
@pytest.mark.parametrize("lazy", [False, True])
def test_can_save_two_names(arches_orm, person_ashs, lazy):
    asha = person_ashs.name.append()
    asha.full_name = "Asha"
    assert len(person_ashs.name) == 2
    person_ashs.save()
    assert len(person_ashs.name) == 2

    reloaded_person = arches_orm.models.Person.find(person_ashs.id, lazy=lazy)
    assert len(reloaded_person.name) == 2
    full_names = {name.full_name for name in reloaded_person.name}
    assert full_names == {"Ash", "Asha"}

@pytest.mark.django_db
@context_free
@pytest.mark.parametrize("lazy", [False, True])
def test_can_save_a_surname(arches_orm, person_ashs, lazy):
    asha = person_ashs.name.append()
    asha.surnames.surname = "Ashb"
    person_ashs.save()

    reloaded_person = arches_orm.models.Person.find(person_ashs.id, lazy=lazy)
    assert reloaded_person.name[1].surnames.surname == "Ashb"

@pytest.mark.django_db
@context_free
@pytest.mark.parametrize("lazy", [False, True])
def test_can_save_two_related_resources_singly(arches_orm, person_ashs, lazy):
    act_1 = arches_orm.models.Activity()
    person_ashs.favourite_activity = act_1
    act_1.save()
    person_ashs.save()
    assert person_ashs.favourite_activity.id == act_1.id

    reloaded_person = arches_orm.models.Person.find(person_ashs.id, lazy=lazy)
    # FIXME: Arches itself treats single resource instances as lists, so will require
    # work either here or upstream to mitigate this on load.
    assert reloaded_person.favourite_activity[0].id == act_1.id

@pytest.mark.django_db
@context_free
@pytest.mark.parametrize("lazy", [False, True])
def test_can_save_two_related_resources(arches_orm, person_ashs, lazy):
    act_1 = arches_orm.models.Activity()
    person_ashs.associated_activities.append(act_1)
    person_ashs.save()
    assert len(person_ashs.associated_activities) == 1

    reloaded_person = arches_orm.models.Person.find(person_ashs.id, lazy=lazy)
    assert len(reloaded_person.name) == 1
    act_2 = arches_orm.models.Activity()
    reloaded_person.associated_activities.append(act_2)
    reloaded_person.save()
    assert len(reloaded_person.associated_activities) == 2

    reloaded_person = arches_orm.models.Person.find(person_ashs.id, lazy=lazy)
    assert len(reloaded_person.associated_activities) == 2

@pytest.mark.django_db
@context_free
@pytest.mark.parametrize("lazy", [False, True])
def test_can_save_two_related_resources_many_times(arches_orm, lazy):
    Person = arches_orm.models.Person
    for i in range(20):
        person = Person.create()
        ash = person.name.append()
        ash.full_name = "Ash"
        ash.surnames.surname = str(i)
        person.save()

        act_1 = arches_orm.models.Activity()
        person.associated_activities.append(act_1)
        person.save()
        assert len(person.associated_activities) == 1

        reloaded_person = arches_orm.models.Person.find(person.id, lazy=lazy)
        assert len(reloaded_person.name) == 1
        act_2 = arches_orm.models.Activity()
        reloaded_person.associated_activities.append(act_2)
        reloaded_person.save()
        assert len(reloaded_person.associated_activities) == 2

        reloaded_person = arches_orm.models.Person.find(person.id, lazy=lazy)
        assert len(reloaded_person.associated_activities) == 2

@pytest.mark.django_db
@context_free
@pytest.mark.parametrize("lazy", [False, True])
def test_unsaved_json(person_ash, lazy):
    resource = person_ash._.to_resource()
    assert resource.to_json() == json.loads(JSON_PERSON)

@pytest.mark.django_db
@context_free
@pytest.mark.parametrize("lazy", [False, True])
def test_find(arches_orm, person_ashs, lazy):
    reloaded_person = arches_orm.models.Person.find(person_ashs.id, lazy=lazy)
    assert reloaded_person.name[0].full_name == "Ash"

@pytest.mark.django_db
@context_free
@pytest.mark.parametrize("lazy", [False, True])
def test_empty_node_is_falsy(arches_orm, person_ashs, lazy):
    assert not person_ashs.user_account

@pytest.mark.django_db
@context_free
@pytest.mark.parametrize("lazy", [False, True])
def test_user_account(arches_orm, person_ashs, lazy):
    from django.contrib.auth.models import User
    user_account = User(email="ash@example.com")
    user_account.save()
    person_ashs.user_account = user_account
    assert person_ashs.user_account.email == "ash@example.com"

    person_ashs.save()

    reloaded_person = arches_orm.models.Person.find(person_ashs.id, lazy=lazy)
    assert reloaded_person.user_account.email == "ash@example.com"

    reloaded_person = arches_orm.models.Person.first(user_account=user_account.id, lazy=lazy, case_i=True)
    assert reloaded_person.user_account.email == "ash@example.com"

@pytest.mark.django_db
@context_free
@pytest.mark.parametrize("lazy", [False, True])
def test_hooks_setup(arches_orm, lazy):
    hooks = arches_orm.add_hooks()
    assert hooks == {"post_save", "post_delete", "post_init"}

@pytest.mark.django_db
@context_free
@pytest.mark.parametrize("lazy", [False, True])
def test_can_create_create_by_class_name(arches_orm, lazy):
    from arches_orm.wkrm import get_well_known_resource_model_by_class_name
    Person = get_well_known_resource_model_by_class_name("Person")
    assert Person == arches_orm.models.Person

@pytest.mark.django_db
@context_free
@pytest.mark.parametrize("lazy", [False, True])
def test_can_retrieve_by_resource_id(arches_orm, person_ashs, lazy):
    from arches_orm.wkrm import attempt_well_known_resource_model
    person = attempt_well_known_resource_model(person_ashs.id, lazy=lazy)
    assert person.__eq__(person_ashs)

@pytest.mark.django_db
@context_free
@pytest.mark.parametrize("lazy", [False, True])
def test_can_attach_related(arches_orm, person_ashs, lazy):
    activity = arches_orm.models.Activity()
    person_ashs.associated_activities.append(activity)
    assert len(person_ashs.associated_activities) == 1

@pytest.mark.django_db
@context_free
@pytest.mark.parametrize("lazy", [False, True])
def test_can_attach_related_then_save(arches_orm, person_ashs, lazy):
    activity = arches_orm.models.Activity()
    person_ashs.associated_activities.append(activity)
    assert len(person_ashs.associated_activities) == 1
    person_ashs.save()
    assert len(person_ashs.associated_activities) == 1
    reloaded_person = arches_orm.models.Person.find(person_ashs.id)
    assert len(reloaded_person.associated_activities) == 1
    assert isinstance(reloaded_person.associated_activities[0], arches_orm.models.Activity)
