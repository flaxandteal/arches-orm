from django.db.models import Func, F, ExpressionWrapper, FloatField, DateTimeField, CharField, OuterRef, Subquery, Case, Value, When, Q
from arches.app.models.models import Value as ValuesModel
from typing import Dict, List
from arches.app.models.models import Node
from django.db import connection
from datetime import datetime
from django.conf import settings
from arches_orm.arches_django.query_builder.config import RESOURCE_MERGED_TILE_DATA_KEY
from typing import TypedDict
from arches_orm.arches_django.query_builder.django import CustomDateTimeField;

class ExpressionDomainValueReturnType(TypedDict):
    default: F
    annotation: ExpressionWrapper

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

def expression_resource_instance_list_datatype(database_engine: str, nodeid: str, additional_keys: List[str] = None) -> ExpressionWrapper | F:
    """
    Method handles using the correct method depending on the database engine
    """
    from .expressions_postgresql import postgresql_expression_resource_instance_list_datatype
    from .expressions_sqlite import sqlite_expression_resource_instance_list_datatype

    if 'postgresql' in database_engine:
        return postgresql_expression_resource_instance_list_datatype(nodeid, additional_keys)

    elif 'sqlite' in database_engine :
        return sqlite_expression_resource_instance_list_datatype(nodeid)


def expression_string_datatype(database_engine: str, nodeid: str, additional_keys: List[str] = None) -> ExpressionWrapper | F:
    """
    Method handles using the correct method depending on the database engine
    """
    from .expressions_postgresql import postgresql_expression_string_datatype
    from .expressions_sqlite import sqlite_expression_string_datatype

    if 'postgresql' in database_engine:
        return postgresql_expression_string_datatype(nodeid, additional_keys)

    elif 'sqlite' in database_engine :
        return sqlite_expression_string_datatype(nodeid, additional_keys)

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

def expression_domain_value(database_engine: str, node: Node, additional_keys: List[str] = None) -> ExpressionDomainValueReturnType:
    from .expressions_postgresql import postgresql_expression_domain_value

    if 'postgresql' in database_engine:
        return postgresql_expression_domain_value(node, additional_keys)

    elif 'sqlite' in database_engine :
        raise Exception("There is no domain value expression setup towards SQLite database")

    # key_lang = additional_keys[0] if additional_keys and len(additional_keys) >= 1 else 'en'
    # options = node.config.get('options', [])
    # dynamic_annotation_key = domain_value_annotation_key(node.alias)

    # when_conditions = []
    # for option in options:
    #     node_id = option.get("id")
    #     selected_option = option['text'][key_lang]

    #     when_conditions.append(
    #         When(**{dynamic_annotation_key: node_id}, then=Value(selected_option))
    #     )

    # case_expression = Case(*when_conditions, default=Value(None))

    # return {
    #     "default": F(f'{RESOURCE_MERGED_TILE_DATA_KEY}__{node.nodeid}'),
    #     "annotation": ExpressionWrapper(
    #         case_expression,
    #         output_field=CharField()
    #     )
    # }


def expression_date_datatype(node: str) -> ExpressionWrapper:
    """
    Converts a string-based date stored in `resource_merged_tile_data__{nodeid}` into a proper DateTimeField 
    for sorting, based on the database backend.
    """
    field = f'{RESOURCE_MERGED_TILE_DATA_KEY}__{node.nodeid}'
    return ExpressionWrapper(F(field), output_field=CustomDateTimeField())

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