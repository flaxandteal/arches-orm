from tests.utilities.common import create_tile_from_model
from typing import TypedDict
from typing import Dict, List;

class SeederSeedDataypes(TypedDict):
    key: str
    seeder: any

class Seeder:
    _datatype_node_alias_keys: Dict[str, List[str]] = None;
    _instance_arches_orm_model: any = None;
    _path_seed: str

    def __init__(self, instance_arches_orm_model: any, datatype_node_alias_keys: Dict[str, List[str]], path_seed: str):
        self._datatype_node_alias_keys = datatype_node_alias_keys
        self._instance_arches_orm_model = instance_arches_orm_model
        self._path_seed = path_seed

    def get_nested_datatype_value(self, record: any, key_path: str) -> any:
        """
        This method has the purpose of getting a value from a nested datatype value for example when we get the full name from a record we would have to
        record.name.full_name and this is not dynamic to have defined in testing, thus this method creation. We instead define the record in the method
        and the datatype key to find, which should be defined in default/consts.py so as an example get_nested_datatype_value(record, 'string')

        Args:
            record (any): This is the record gained from the arches orm model so a WKRI instance
            key_path (str): This is the key towards a first level within consts structure, therefore we gain the keys required to access the datatype value

        Returns:
            any: This returns the datatype value gained from the record
        """
        
        keys = self._datatype_node_alias_keys[key_path]

        for key in keys:
            record = record.get(key) 
            if record is None: return None 
            
        return record

    def seed(self, amount: int, seed_datatypes: SeederSeedDataypes):
        """
        Method handles the seeding towards a arches orm model, for example Person.create(). The model and the datatype keys are defined within the __init__
        method, therefore we can just access these, however we still need the amount of resources needed created and seed_datatypes for example
        towards seed_datatypes, we would use { 'string': 'TEST1' } or { 'string': None } or { 'string': custom_callback_method() }

        Args:
            amount (int): The amount of resources the user wishes to create
            seed_datatypes (SeederSeedDataypes): Here are some examples { 'string': 'TEST1' } or { 'string': None } or { 'string': custom_callback_method() }
                but the main purpose is to have custom values for certain datatype values within the resource
        """

        includes = []
        seeds = {}

        if (seed_datatypes):
            for datatype, seeder in seed_datatypes.items():
                if datatype in self._datatype_node_alias_keys:
                    keys = self._datatype_node_alias_keys[datatype]
                    includes.extend(keys)

                    if seeder:
                        seeds[keys[-1]] = seeder

        resources = [];

        for index in range(amount):
            resource = create_tile_from_model(
                self._instance_arches_orm_model.create(), 
                path_seed=self._path_seed,
                includes=includes,
                custom_seed_values=seeds,
                loop_index=index
            )
            resource.save() 
            resources.append(resource)

        return resources