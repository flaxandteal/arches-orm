from django.db import connection
from typing import List, Dict
from arches_orm.view_models import SemanticViewModel, NodeListViewModel, StringViewModel
from pathlib import Path
from arches.app.utils.betterJSONSerializer import JSONDeserializer
import random
import string

def print_table_data(table_name: str):
    """
    Method handles printing all the table data out in the console. This method mainly should be used towards developing test cases

    Args:
        table_name (str): The table name
    """
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT * FROM {table_name};")
        rows = cursor.fetchall()

        column_names = [description[0] for description in cursor.description]

        for row in rows:
            row_dict = dict(zip(column_names, row))
            print(row_dict) 
            print('---------------------------------------------------------------')

def create_tile_from_model(
        model,
        path_seed: str,
        custom_seed_values: Dict[str, any] | None = None,
        excludes: List[str] | None = None, 
        includes: List[str] | None = None,
        loop_index: int = None
    ):
    """
    This method creates the nodes towards tiles. Within the 

    Args:
        model (any): This is the arches model for create for example Person.create()
        path_seed (str): This is the path towards the graph.json file on the directory
        custom_seed_values (Dict[str, any] | None): This is for custom values on certain keys for example full_name should equal 'Ben'
        excludes (List[str] | None, optional): This is the node keys alias to exclude from seeding
        includes (List[str] | None, optional): This is the node keys alias to include towards seeding
        loop_index (int): This is gained from the a loop index for example the amount of resources wanted created

    Returns:
        any: Returns the model with datatypes updated
    """
    processed_recursive_keys = [];
    nodes = get_nodes_by_key(path_seed, 'alias');

    def recursive(model):
        """
        This method handles the setting of values towards the model's datatypes and the recursiveness if the model's datatype has more inner datatypes

        Args:
            model (any): This is the arches model for create for example Person.create()

        Returns:
            any: Returns the model with datatypes updated
        """

        nonlocal includes, excludes;

        for key in model._child_keys:
            # * BASE CASES
            if (includes and len(includes) > 0 and key not in includes):
                continue;
            
            if (excludes and len(excludes) > 0 and key in excludes):
                continue;
            
            if (key in processed_recursive_keys):
                return;
            
            processed_recursive_keys.append(key)
            datatype = getattr(model, key, "Attribute not found")

            if (isinstance(datatype, NodeListViewModel)):
                datatype = datatype.append()

            if (isinstance(datatype, SemanticViewModel)):
                model.update({key: recursive(datatype)})
                continue



            def _datatype_seeders():
                if (custom_seed_values and key in custom_seed_values and custom_seed_values[key] is not None):
                    if (callable(custom_seed_values[key])):
                        model.update({key: custom_seed_values[key](loop_index)})
                    else:
                        model.update({key: custom_seed_values[key]})

                else:
                    datatype_type = nodes[key]['datatype'];

                    if datatype_type == 'string':
                        characters = string.ascii_letters + string.digits
                        value = ''.join(random.choices(characters, k=random.randrange(5, 10)))
                        model.update({key: value })
                
                    elif datatype_type == 'number':
                        setattr(model, key, random.randrange(1,100))

                    elif datatype_type == 'domain-value':
                        model.update({key: '049d0b2c-b2df-43a8-9a7e-855c7abc42dc'})

                    # * Selects a random concept within the Collection List
                    elif datatype_type == 'concept':
                        CollectionEnum = model.__collection__
                        model.update({key: random.choice(list(CollectionEnum)) })

                    # * Selects random concepts within the Collection List
                    elif datatype_type == 'concept-list':
                        CollectionEnum = model.__collection__
                        num_conecpts = random.randint(1, len(CollectionEnum))
                        random_concepts = random.sample(list(CollectionEnum), num_conecpts)
                        model.update({key: random_concepts });
            
                    elif datatype_type == 'boolean':
                        model.update({key: random.choice(["TRUE", "FALSE"])})
                   
            _datatype_seeders()
        return model

    model = recursive(model)
    return model
    

def get_nodes_by_key(path_seed: str, key: str) -> Dict[str, any]:
    """
    This method gets all the nodes and does a by key for example alias or nodeid

    Args:
        path_seed (str): The seed set type within the seed folder
        key (str): The key to use as a key within the node for example alias, nodeid, etc.

    Returns:
        Dict[str, any]: The custom node key used as the key and the node as the value
    """
    with (Path(__file__).parent.parent / "arches_django/seed" / path_seed / 'graph.json').open("r") as f:
        archesfile = JSONDeserializer().deserialize(f)
        nodes = archesfile["graph"][0]['nodes']

        return {node[key]: node for node in nodes}