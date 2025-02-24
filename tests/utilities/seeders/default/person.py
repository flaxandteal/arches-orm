from tests.utilities.common import create_tile_from_model
import random
from datetime import datetime, timedelta
from typing import TypedDict

person_datatype_node_alias_keys = {
    'domain-value': [
            'family_members', 
                'family_members_amount'
        ],
    'string': [
        'family_members',
            'pet'
    ],
    'number': [
        'system_reference_numbers', 
            'primaryreferencenumber',
                'primary_reference_number'
    ],
    'date': [
        'audit_metadata', 
            'audit_creation',
                'creation_timespan',
                    'creation_end_date'
    ]
}

class PersonSeederSeedDataypes(TypedDict):
    key: str
    seeder: any

def get_nested_datatype_value(record: any, key_path: str) -> any:
    keys = person_datatype_node_alias_keys[key_path]

    for key in keys:
        record = record.get(key) 
        if record is None:
            return None 
        
    return record

def person_seeder(model, amount: int, seed_datatypes: PersonSeederSeedDataypes):
    includes = []
    seeds = {}

    for datatype, seeder in seed_datatypes.items():
        if datatype in person_datatype_node_alias_keys:
            keys = person_datatype_node_alias_keys[datatype]
            includes.extend(keys)

            if seeder:
                seeds[keys[-1]] = seeder

    print('includes : ', includes)

    for index in range(amount):
        print('INDEX CREATING : ', index)
        resource = create_tile_from_model(
            model.create(), 
            includes=includes,
            custom_seed_values=seeds,
            loop_index=index
        )
        resource.save() 