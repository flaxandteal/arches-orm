from django.test import override_settings
from django.test import TestCase
from django.contrib.auth.models import User
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


@pytest.mark.django_db
def test_startup(arches_orm):
    Person = arches_orm.models.Person
    person = Person.create()
    ash = person.name.append()
    ash.full_name = "Ash"
    resource = person.to_resource()

    assert resource.to_json() == json.loads(JSON_PERSON)

    person.save()

    reloaded_person = Person.find(person.id)
    assert reloaded_person.name[0].full_name == "Ash"

    user_account = User(email="ash@example.com")
    user_account.save()
    reloaded_person.user_account = user_account
    assert reloaded_person.user_account.email == "ash@example.com"

    reloaded_person.save()

    reloaded_person = Person.find(person.id)
    assert reloaded_person.user_account.email == "ash@example.com"
