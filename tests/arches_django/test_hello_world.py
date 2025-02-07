import pytest
import json
from uuid import UUID
from arches_orm.adapter import context_free, get_adapter
from arches_orm.utils import string_to_enum
from arches_orm.errors import DescriptorsNotYetSet
from django.db import connection
from tests.utilities.asserts.datatypes import assert_datatype_semmantic
from arches.app.utils.betterJSONSerializer import JSONDeserializer
from pathlib import Path
from typing import List
from arches_orm.view_models import SemanticViewModel, NodeListViewModel, StringViewModel
from tests.utilities.common import create_tile_from_nodes

def arches_import_method():
    from arches.app.utils.data_management.resources.importer import BusinessDataImporter
    from django.test.utils import captured_stdout
    
    with captured_stdout():
        BusinessDataImporter(
            "tests/arches_django/seed/default/cars/business-data.json"
        ).import_business_data()

@context_free
def test_can_save_with_name(arches_orm):

    # ! Need a way to check an entire resource query to make sure it the correct datatypes
    # ! Need a way to create a person each time
    # ! We can use the alias and the alis within the graph id to create a mapping system
    Person = arches_orm.models.Person

    # death
    # external_cross_references
    # contact_details
    # django_group
    # audit_metadata
    # name
    # descriptions
    # location_data
    # images
    # system_reference_numbers
    # user_account
    # associated_actors
    # currency
    # associated_monuments_areas_and_artefacts
    # resource_model_type
    # birth
    # favourite_activity
    # associated_activities
    # nismr_numbering_type

    # avoid_keys = ['death']

    includes = ['name', 'full_name']

    person = create_tile_from_nodes(Person.create(), includes=includes)
    person.save()

    print(Person.all()[0].name[0].full_name)

    # ash = person.dwa.append()
    # ash.full_name = "Ash"
    # print(type(ash.full_name).__name__)
    # external_cross_references - Semnatic

    # (['death', 'external_cross_references', 'contact_details', 'django_group', 'audit_metadata', 'name', 'descriptions', 'location_data', 'images',

    # person.save()

    # print(Person.all()[0].dwadwa)

    # nodes_by_node_alias = get_nodes_by_node_alias('person')


    # print(Person.all()[0])

    # assert_datatype_semmantic(Person.all()[0].external_cross_references)

    # arches_import_method()

