from django.db.models import Func, F, ExpressionWrapper, FloatField, CharField, DateTimeField, OuterRef, Subquery, BooleanField
from arches.app.models.models import Value as ValuesModel
from typing import Dict, List
from arches.app.models.models import Node
from django.db import connection
from datetime import datetime
from django.conf import settings

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
    return F(f'data__{nodeid}')

def expression_domain_value(node: Node, addional_keys: List[str] = None) -> ExpressionWrapper:
    print(node.config.get("dateFormat"))
    key_lang = addional_keys[0] if len(addional_keys) >= 1 else 'en'
    value_lang = addional_keys[1] if len(addional_keys) >= 2 else 'value'

def expression_date_datatype(nodeid: str) -> ExpressionWrapper:
    """
    Converts a string-based date stored in `data__{nodeid}` into a proper DateTimeField 
    for sorting, based on the database backend.
    """
    return ExpressionWrapper(
        F(f'data__{nodeid}'),
        output_field=DateTimeField()
    )

def expression_concept_value(node: Node):
    from arches.app.models.concept import Concept

    concept_id = node.config.get('rdmCollection')
    print('ABOVE : ', ValuesModel.objects.filter(concept_id=concept_id))
    # print('INSIDE NODE ID : ', node.nodeid)    
    # collection = Concept().get(id=)

    return ExpressionWrapper(
        Subquery(
            ValuesModel.objects.filter(valueid=OuterRef(f'data__{node.nodeid}')).values('value')[:1]
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