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

    includes = [
        "name",
        "full_name"
    ]

    for _ in range(50):  # Loops from 0 to 2
        person = create_tile_from_nodes(Person.create(), includes=includes)
        person.save()

    assert(len(Person.all(page=None)) == 50)

def create_tile_from_nodes(model, includes: List[str] | None = None, excludes: List[str] | None = None):
    """
    Method creates a single resource with automatic tile definations

    Args:
        model (any): This is returned from create() method on a wkrm
        includes (List[str] | None, optional): This is the list of node alias which are whitelisted only to create tile data from
        excludes (List[str] | None, optional): This is the list of node alias which are blacklisted only to create tile data from

    Returns:
        any: Returns the method got from created() but the tile values are updated 
    """

    processed_recursive_keys: List[str] = [];

    def recursive(datatype, includes: List[str] | None = None, excludes: List[str] | None = None):

        print('DATATYPE: ', type(datatype).__name__)

        for key in datatype._child_keys:
            """ BASE CASES """
            if (includes and len(includes) > 1 and key not in includes): 
                continue;
            
            if (excludes and len(excludes) > 1 and key in excludes): 
                continue;
            
            if (key in processed_recursive_keys):
                return;
            
            processed_recursive_keys.append(key)

            """ CHECK FOR RECURSIVE FLOW"""
            if (isinstance(datatype[key], NodeListViewModel)):
                semmanticNode = datatype[key].append()

                if (isinstance(semmanticNode, SemanticViewModel)):
                    recursive(semmanticNode, includes)

            elif (isinstance(datatype[key], SemanticViewModel)):
                recursive(datatype[key], includes)

            """ SET DATATYPE VALUES """
            if (isinstance(datatype[key], StringViewModel)):
                setattr(datatype, key, random_string())

        return datatype
    
    model = recursive(model, includes, excludes)

    return model

def random_string():
    import random
    import string

    length = random.randint(5, 10)  # Random length between 1 and 10
    return ''.join(random.choices(string.ascii_letters, k=length))

def get_nodes_key_by(seed_set: str, key: str):
    with (Path(__file__).parent / "seed/default" / seed_set / 'graph.json').open("r") as f:
        archesfile = JSONDeserializer().deserialize(f)
        nodes = archesfile["graph"][0]['nodes']

        return {node['nodeid']: node for node in nodes}