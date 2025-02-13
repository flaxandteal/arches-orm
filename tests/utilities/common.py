from django.db import connection
from typing import List, Dict
from arches_orm.view_models import SemanticViewModel, NodeListViewModel, StringViewModel
from pathlib import Path
from arches.app.utils.betterJSONSerializer import JSONDeserializer
import random

def printTables():
    with connection.cursor() as cursor:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

    print(tables)

def create_tile_from_model(
        model,
        custom_seed_values: Dict[str, any] | None = None,
        excludes: List[str] | None = None, 
        includes: List[str] | None = None
    ):
    """
    This method creates the nodes towards tiles

    Args:
        model (any): This is the arches model for create for example Person.create()
        excludes (List[str] | None, optional): This is the node keys alias to exclude from seeding
        includes (List[str] | None, optional): This is the node keys alias to include towards seeding

    Returns:
        any: Returns the model with datatypes updated
    """
    processed_recursive_keys = [];
    nodes = get_nodes_by_key('person', 'alias');

    def recursive(model):
        """
        This method handles the setting of values towards the model's datatypes and the recursiveness if the model's datatype has more inner datatypes

        Args:
            model (any): This is the arches model for create for example Person.create()
            excludes (List[str] | None, optional): This is the node keys alias to exclude from seeding
            includes (List[str] | None, optional): This is the node keys alias to include towards seeding

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

            def recursive_handling():
                nonlocal datatype

                if (isinstance(datatype, NodeListViewModel)):
                    datatype = datatype.append()

                if (isinstance(datatype, SemanticViewModel)):
                    recursive(datatype)

            def datatype_seeders():
                nonlocal datatype, model, key, nodes, custom_seed_values

                if (custom_seed_values and key in custom_seed_values):
                    if (callable(custom_seed_values[key])):
                        setattr(model, key, custom_seed_values[key]())
                    else:
                        setattr(model, key, custom_seed_values[key])

                    return;
            
                datatype_type = nodes[key]['datatype'];
                    
                if datatype_type == 'string':
                    setattr(model, key, _handle_value_string_view_model());
            
                elif datatype_type == 'number':
                    setattr(model, key, random.randrange(1,1000))
        
            recursive_handling()
            datatype_seeders()
        

                
        return model

    model = recursive(model)

    return model
    

def get_nodes_by_key(seed_set: str, key: str) -> Dict[str, any]:
    """
    This method gets all the nodes and does this by key for example alias or nodeid

    Args:
        seed_set (str): The seed set type within the seed folder
        key (str): The key by key

    Returns:
        _type_: The
    """
    with (Path(__file__).parent.parent / "arches_django/seed/default" / seed_set / 'graph.json').open("r") as f:
        archesfile = JSONDeserializer().deserialize(f)
        nodes = archesfile["graph"][0]['nodes']

        return {node[key]: node for node in nodes}
    
def _handle_value_string_view_model(length=10):
    import random
    import string

    characters = string.ascii_letters + string.digits
    return ''.join(random.choices(characters, k=length))