from django.test import override_settings
from django.test import TestCase
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
            "Full Name": null,
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
        },
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
            "Full Name": null,
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
    Person = arches_orm.Person
    person = Person.create(name="Ash")
    assert person.name == "Ash"
    resource = person.to_resource()

    assert resource.to_json() == json.loads(JSON_PERSON)
