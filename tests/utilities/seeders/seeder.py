from tests.utilities.common import create_tile_from_model
from typing import TypedDict

class SeederSeedDataypes(TypedDict):
    key: str
    seeder: any

class Seeder:
    _datatype_node_alias_keys = None;
    _instance_arches_orm_model = None;

    def __init__(self, instance_arches_orm_model: any, datatype_node_alias_keys):
        self._datatype_node_alias_keys = datatype_node_alias_keys
        self._instance_arches_orm_model = instance_arches_orm_model

    def get_nested_datatype_value(self, record: any, key_path: str) -> any:
        keys = self._datatype_node_alias_keys[key_path]

        for key in keys:
            record = record.get(key) 
            if record is None:
                return None 
            
        return record

    def seed(self, amount: int, seed_datatypes: SeederSeedDataypes):
        includes = []
        seeds = {}

        if (seed_datatypes):
            for datatype, seeder in seed_datatypes.items():
                if datatype in self._datatype_node_alias_keys:
                    keys = self._datatype_node_alias_keys[datatype]
                    includes.extend(keys)

                    if seeder:
                        seeds[keys[-1]] = seeder

        for index in range(amount):
            resource = create_tile_from_model(
                self._instance_arches_orm_model.create(), 
                includes=includes,
                custom_seed_values=seeds,
                loop_index=index
            )
            print('RESOURECE: ', resource.family_members.cars)
            resource.save() 