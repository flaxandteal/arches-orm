import pytest
import json
from uuid import UUID
from arches_orm.adapter import context_free, get_adapter
from arches_orm.utils import string_to_enum
from arches_orm.errors import DescriptorsNotYetSet
from django.db import connection

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