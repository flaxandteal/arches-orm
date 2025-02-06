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

def arches_import_method():
    from arches.app.utils.data_management.resources.importer import BusinessDataImporter
    from django.test.utils import captured_stdout
    
    with captured_stdout():
        BusinessDataImporter(
            "tests/arches_django/seed/default/cars/business-data.json"
        ).import_business_data()

@context_free
def test_can_save_with_name(arches_orm):
    Hobbies = arches_orm.models.Hobbies
    print(len(Hobbies.all()))

    # arches_import_method()

