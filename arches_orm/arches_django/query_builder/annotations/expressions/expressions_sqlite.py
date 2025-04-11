from django.db.models import Func, F, ExpressionWrapper, FloatField, CharField, DateTimeField, OuterRef, Subquery, BooleanField, JSONField, Value
from arches.app.models.models import Value as ValuesModel
from typing import Dict, List
from arches.app.models.models import Node
from django.db import connection
from datetime import datetime
from django.conf import settings
from django.db.models.aggregates import Aggregate
from arches_orm.arches_django.query_builder.config import RESOURCE_MERGED_TILE_DATA_KEY

class JsonGroupArray(Aggregate):
    function = 'JSON_GROUP_ARRAY'
    output_field = JSONField()
    template = '%(function)s(%(distinct)s%(expressions)s)'

class JsonExtract(Func):
    function = 'json_extract'
    output_field = JSONField()
    template = "json_extract(%(expressions)s, '$[0]')"

merged_json_data_key = 'merged_json_data'

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
        F(f'{RESOURCE_MERGED_TILE_DATA_KEY}__{nodeid}'),
        output_field=JSONField()
    )

def sqlite_expression_merge_tile_json_data():
    return JsonGroupArray(F('data'))

def sqlite_expression_after_merge_extract_json():
    return JsonExtract(F(merged_json_data_key))

def sqlite_default_fallback_expression_generic(nodeid: str) -> F:
    """
    Method used as a fallback which will work when psql can determine the query without an expression wrapper

        Args:
        nodeid (str): The node id

    Returns:
        F: This is the expression that is returned and should be mainly used for annotations

    """
    return F(f'{RESOURCE_MERGED_TILE_DATA_KEY}__{nodeid}')

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

    key_lang = addional_keys[0] if addional_keys and len(addional_keys) >= 1 else 'en'
    value_lang = addional_keys[1] if addional_keys and len(addional_keys) >= 2 else 'value'

    return ExpressionWrapper(
        F(f'{RESOURCE_MERGED_TILE_DATA_KEY}__{nodeid}__{key_lang}__{value_lang}'),
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
        F(f'{RESOURCE_MERGED_TILE_DATA_KEY}__{nodeid}'),
        output_field=FloatField()
    )