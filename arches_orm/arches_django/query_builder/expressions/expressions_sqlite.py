from django.db.models import Func, F, ExpressionWrapper, FloatField, CharField, DateTimeField, OuterRef, Subquery, BooleanField, JSONField
from arches.app.models.models import Value as ValuesModel
from typing import Dict, List
from arches.app.models.models import Node
from django.db import connection
from datetime import datetime
from django.conf import settings

def sqlite_expression_resource_instance_list_datatype(nodeid: str) -> ExpressionWrapper:
    """
    Method gets the experssion for a resource-instance-list datatype. This is mainaly used for the tiles JSON column that is stored within the database so we can use
    annotations around the expressions

    Args:
        nodeid (str): The node id

    Returns:
        ExpressionWrapper: This is the expression wrapper that is returned and should be mainly used for annotations
    """

    return ExpressionWrapper(
        F(f'data__{nodeid}'),
        output_field=JSONField()
    )

def sqlite_default_fallback_expression_generic(nodeid: str) -> F:
    """
    Method used as a fallback which will work when psql can determine the query without an expression wrapper

        Args:
        nodeid (str): The node id

    Returns:
        F: This is the expression that is returned and should be mainly used for annotations

    """
    return F(f'data__{nodeid}')

def sqlite_expression_string_datatype(nodeid: str, addional_keys: List[str] = None) -> ExpressionWrapper:
    """
    Method gets the experssion for a string datatype. This is mainaly used for the tiles JSON column that is stored within the database so we can use
    annotations around the expressions

    Args:
        nodeid (str): The node id
        addional_keys (List[str], optional): The addional keys are used towards the user input for example firstname__en='Harry'. Defaults to None.

    Returns:
        ExpressionWrapper: This is the expression wrapper that is returned and should be mainly used for annotations
    """

    key_lang = addional_keys[0] if len(addional_keys) >= 1 else 'en'
    value_lang = addional_keys[1] if len(addional_keys) >= 2 else 'value'

    return ExpressionWrapper(
        F(f'data__{nodeid}__{key_lang}__{value_lang}'),
        output_field=CharField()
    )

def sqlite_expression_number_datatype(nodeid: str) -> ExpressionWrapper:
    """
    Method gets the experssion for a number datatype. This is mainaly used for the tiles JSON column that is stored within the database so we can use
    annotations around the expressions

    Args:
        nodeid (str): The node id

    Returns:
        ExpressionWrapper: This is the expression wrapper that is returned and should be mainly used for annotations
    """

    return ExpressionWrapper(
        F(f'data__{nodeid}'),
        output_field=FloatField()
    )