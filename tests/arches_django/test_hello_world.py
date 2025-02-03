import pytest
import json
from uuid import UUID
from arches_orm.adapter import context_free, get_adapter
from arches_orm.utils import string_to_enum
from arches_orm.errors import DescriptorsNotYetSet
from django.db import connection

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

def printTables():
    with connection.cursor() as cursor:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

    print(tables)  # This will show all tables in the database

@context_free
def test_can_save_with_name(arches_orm):
    print('HELLO WORLD!')
    print('BELOW!')
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM graphs LIMIT 5;")  # Show data
        # print(cursor.fetchall())
    print(vars(arches_orm.models))

    Person = arches_orm.models.Person
    print(len(Person.all()))
    # person = Person.create()
    # ash = person.name.append()
    # ash.full_name = "Ash"
    # person.save()