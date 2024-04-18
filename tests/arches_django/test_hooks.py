import pytest
from collections import Counter
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


@pytest.mark.django_db
def test_can_save_with_name(arches_orm):
    Person = arches_orm.models.Person
    person = Person.create()
    ash = person.name.append()
    ash.full_name = "Ash"
    person.save()

@pytest.mark.django_db
def test_can_hook_saving_relationship(arches_orm, person_ashs):
    from arches_orm import add_hooks
    add_hooks()

    calls = Counter()
    def activity_related(sender, reason=None, **kwargs):
        assert reason == "relationship-to saved"
        calls["activity"] += 1

    def person_related(sender, **kwargs):
        assert reason == "relationship-to saved"
        calls["person"] += 1

    arches_orm.models.Activity.post_related_to.connect(activity_related)
    arches_orm.models.Person.post_related_to.connect(person_related)

    expected_activity_calls = 0

    act_1 = arches_orm.models.Activity()
    person_ashs.associated_activities.append(act_1)
    person_ashs.save()
    expected_activity_calls += 1
    assert len(person_ashs.associated_activities) == 1
    assert calls["activity"] == expected_activity_calls

    reloaded_person = arches_orm.models.Person.find(person_ashs.id)
    assert len(reloaded_person.name) == 1
    act_2 = arches_orm.models.Activity()
    reloaded_person.associated_activities.append(act_2)
    reloaded_person.save()
    expected_activity_calls += 2
    assert len(reloaded_person.associated_activities) == 2

    # One call for original as well.
    assert calls["activity"] == expected_activity_calls

    reloaded_person = arches_orm.models.Person.find(person_ashs.id)
    assert len(reloaded_person.associated_activities) == 2

    assert calls["activity"] == expected_activity_calls
    assert calls["person"] == 0
