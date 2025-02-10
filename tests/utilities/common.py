from django.db import connection
from typing import List, Dict
from arches_orm.view_models import SemanticViewModel, NodeListViewModel, StringViewModel
from pathlib import Path
from arches.app.utils.betterJSONSerializer import JSONDeserializer

def printTables():
    with connection.cursor() as cursor:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

    print(tables)

def create_tile_from_model(model, excludes: List[str] | None = None, includes: List[str] | None = None):
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

    def recursive(model, excludes: List[str] | None = None, includes: List[str] | None = None):
        """
        This method handles the setting of values towards the model's datatypes and the recursiveness if the model's datatype has more inner datatypes

        Args:
            model (any): This is the arches model for create for example Person.create()
            excludes (List[str] | None, optional): This is the node keys alias to exclude from seeding
            includes (List[str] | None, optional): This is the node keys alias to include towards seeding

        Returns:
            any: Returns the model with datatypes updated
        """


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

            # * RECURSIVE CHECKER
            if (isinstance(datatype, NodeListViewModel)):
                datatype = datatype.append()

            if (isinstance(datatype, SemanticViewModel)):
                recursive(datatype, excludes, includes)

            # * DATATYPE SETTERS
            if (isinstance(datatype, StringViewModel)):
                setattr(model, key, _handle_value_string_view_model());
                
        return model

    model = recursive(model, excludes, includes)

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
    with (Path(__file__).parent / "seed/default" / seed_set / 'graph.json').open("r") as f:
        archesfile = JSONDeserializer().deserialize(f)
        nodes = archesfile["graph"][0]['nodes']

        return {node[key]: node for node in nodes}
    
def _handle_value_string_view_model(length=10):
    import random
    return random.choice(['UP', 'DOWN'])
    import random
    import string

    characters = string.ascii_letters + string.digits
    return ''.join(random.choices(characters, k=length))