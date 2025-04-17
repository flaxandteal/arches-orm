from django.db.models import Func, F, ExpressionWrapper, FloatField, CharField, DateTimeField, OuterRef, Subquery, Case, Value, When, Q
from arches.app.models.models import Value as ValuesModel
from typing import Dict, List
from arches.app.models.models import Node
from django.db import connection
from datetime import datetime
from django.conf import settings
from arches_orm.arches_django.query_builder.config import RESOURCE_MERGED_TILE_DATA_KEY

def _figure_out_field_instance_type(value: str):
    try:
        datetime.fromisoformat(value)
        return DateTimeField
    except:
        pass
    
    try:
        int(value)
        return FloatField
    except:
        pass

    return CharField

def expresion_merge_tile_json_data(database_engine: str):
    """
    Method handles using the correct method depending on the database engine
    """
    from .expressions_postgresql import postgresql_expression_merge_tile_json_data
    from .expressions_sqlite import sqlite_expression_after_merge_extract_json

    if database_engine and 'sqlite' in database_engine:
        return sqlite_expression_after_merge_extract_json()
    
    else:
        return postgresql_expression_merge_tile_json_data()

def expression_generic_default_fallback(database_engine: str, nodeid: str) -> ExpressionWrapper | F:
    """
    Method handles using the correct method depending on the database engine
    """
    from .expressions_postgresql import postgresql_default_fallback_expression_generic
    from .expressions_sqlite import sqlite_default_fallback_expression_generic

    if 'postgresql' in database_engine:
        return postgresql_default_fallback_expression_generic(nodeid)

    elif 'sqlite' in database_engine :
        return sqlite_default_fallback_expression_generic(nodeid)

def expression_resource_instance_list_datatype(database_engine: str, nodeid: str) -> ExpressionWrapper | F:
    """
    Method handles using the correct method depending on the database engine
    """
    from .expressions_postgresql import postgresql_expression_resource_instance_list_datatype
    from .expressions_sqlite import sqlite_expression_resource_instance_list_datatype

    if 'postgresql' in database_engine:
        return postgresql_expression_resource_instance_list_datatype(nodeid)

    elif 'sqlite' in database_engine :
        return sqlite_expression_resource_instance_list_datatype(nodeid)


def expression_string_datatype(database_engine: str, nodeid: str, addional_keys: List[str] = None) -> ExpressionWrapper | F:
    """
    Method handles using the correct method depending on the database engine
    """
    from .expressions_postgresql import postgresql_expression_string_datatype
    from .expressions_sqlite import sqlite_expression_string_datatype

    if 'postgresql' in database_engine:
        return postgresql_expression_string_datatype(nodeid, addional_keys)

    elif 'sqlite' in database_engine :
        return sqlite_expression_string_datatype(nodeid, addional_keys)

# * If I just return the key, the query works as expected where(old_enough=True), however if I return a ExpressionWrapper, this stops working, therefore
# * the return type is F (Just the key)
def expression_boolean_value(nodeid: str) -> F:
    """
    Method handles using a custom key for the datatype booleans

    Args:
        nodeid (str): This is the node ID string

    Returns:
        F: This is the Field which represents a reference into the database and this is used for annotations
    """
    return F(f'{RESOURCE_MERGED_TILE_DATA_KEY}__{nodeid}')

def expression_domain_value(database_engine: str, node: Node, additional_keys: List[str] = None) -> ExpressionWrapper:
    from django.db.models import F, Func, Value, Case, When

    key_lang = additional_keys[0] if additional_keys and len(additional_keys) >= 1 else 'en'
    options = node.config.get('options', [])

    print("\n--- Debug: expression_domain_value ---")
    print("Language key:", key_lang)
    print("Node ID:", node.nodeid)
    print("Options:")
    for opt in options:
        print("  ID:", opt.get("id"), "| Text:", opt.get("text", {}).get(key_lang))

    when_conditions = []
    for option in options:
        node_id = option.get("id")
        label = option.get("text", {}).get(key_lang, "")


        # Reference the actual field (e.g., "tiledata") in the model directly
        # tile_value = Func(
        #     F('tiledata'),  # The field in your model (tiledata or whatever field name you're using)
        #     Value(node_id),  # The key you want to extract from the JSON
        #     function='jsonb_extract_path_text',
        #     template="%(function)s(%(expressions)s)"  # Custom template to extract the path text
        # )

        # print('tile_value', tile_value)
        field_name = f'{RESOURCE_MERGED_TILE_DATA_KEY}__{node.nodeid}'
        print(f"Field_Name : ", field_name)
        print(f"NODE_ID : ", node_id)

        # Directly use the tile_value expression in the When clause
      # Correcting the comparison in the When clause

        # Create the condition
        when_conditions.append(
            When(
                Q(**{field_name: node_id}),
                then=Value("FOUND")
            )
        )

    case_expression = Case(*when_conditions, default=Value(None))

    print("--- End Debug ---\n")
    return ExpressionWrapper(
        case_expression,
        output_field=CharField()
    )
def expression_date_datatype(nodeid: str) -> ExpressionWrapper:
    """
    Converts a string-based date stored in `resource_merged_tile_data__{nodeid}` into a proper DateTimeField 
    for sorting, based on the database backend.
    """
    return ExpressionWrapper(
        F(f'{RESOURCE_MERGED_TILE_DATA_KEY}__{nodeid}'),
        output_field=DateTimeField()
    )

def expression_concept_value(node: Node):
    from arches.app.models.concept import Concept

    concept_id = node.config.get('rdmCollection')
    # print('INSIDE NODE ID : ', node.nodeid)    
    # collection = Concept().get(id=)

    return ExpressionWrapper(
        Subquery(
            ValuesModel.objects.filter(valueid=OuterRef(f'{RESOURCE_MERGED_TILE_DATA_KEY}__{node.nodeid}')).values('value')[:1]
        ),
        output_field=CharField()
    )

    # _figure_out_field_instance_type()

def expression_number_datatype(database_engine: str, nodeid: str) -> ExpressionWrapper | F:
    """
    Method handles the expression or function by checking the database and using the appropriate method 

    Args:
        nodeid (str): The node id

    Returns:
        ExpressionWrapper | F: This is the expression or function used to handle the JSON value key
    """
    from .expressions_postgresql import postgresql_expression_number_datatype
    from .expressions_sqlite import sqlite_expression_number_datatype

    if 'postgresql' in database_engine:
        return postgresql_expression_number_datatype(nodeid)

    elif 'sqlite' in database_engine :
        return sqlite_expression_number_datatype(nodeid)