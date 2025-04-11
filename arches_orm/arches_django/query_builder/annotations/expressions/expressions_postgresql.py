from django.db.models import Func, F, ExpressionWrapper, FloatField, CharField, DateTimeField, OuterRef, Subquery, BooleanField, JSONField
from django.contrib.postgres.fields import JSONField as PostgreSQLJSONField
from arches.app.models.models import Value as ValuesModel
from typing import Dict, List
from arches.app.models.models import Node
from django.db import connection
from datetime import datetime
from django.conf import settings
from django.contrib.postgres.aggregates import JSONBAgg
from arches_orm.arches_django.query_builder.config import RESOURCE_MERGED_TILE_DATA_KEY
from django.db.models.aggregates import Aggregate
from django.db.models.expressions import RawSQL

class JsonBAgg(Aggregate):
    function = 'jsonb_agg'
    output_field = JSONField()
    template = '%(function)s(%(distinct)s%(expressions)s)'

def postgresql_expression_resource_instance_list_datatype(nodeid: str) -> ExpressionWrapper:
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

def postgresql_expression_merge_tile_json_data():
    return RawSQL(
        """
        (
            SELECT jsonb_object_agg(kv.key, kv.value)
            FROM tiles AS t
            JOIN jsonb_each(t.tiledata) AS kv ON true
            WHERE t.resourceinstanceid = tiles.resourceinstanceid
        )
        """, 
        [],
        output_field=PostgreSQLJSONField()  # This is the key fix
    )

def postgresql_default_fallback_expression_generic(nodeid: str) -> F:
    """
    Method used as a fallback which will work when psql can determine the query without an expression wrapper

        Args:
        nodeid (str): The node id

    Returns:
        F: This is the expression that is returned and should be mainly used for annotations

    """
    return F(f'{RESOURCE_MERGED_TILE_DATA_KEY}__{nodeid}')

def postgresql_expression_string_datatype(nodeid: str, addional_keys: List[str] = None) -> F:
    """
    Method gets the experssion for a string datatype. This is mainaly used for the tiles JSON column that is stored within the database so we can use
    annotations around the expressions

    Args:
        nodeid (str): The node id
        addional_keys (List[str], optional): The addional keys are used towards the user input for example firstname__en='Harry'. Defaults to None.

    Returns:
        F: This is the function used to get the value
    """

    key_lang = addional_keys[0] if addional_keys and len(addional_keys) >= 1 else 'en'
    value_lang = addional_keys[1] if addional_keys and len(addional_keys) >= 2 else 'value'

    return  F(f'{RESOURCE_MERGED_TILE_DATA_KEY}__{nodeid}__{key_lang}__{value_lang}')

def postgresql_expression_number_datatype(nodeid: str) -> F:
    """
    Method gets the experssion for a number datatype. This is mainaly used for the tiles JSON column that is stored within the database so we can use
    annotations around the expressions

    Args:
        nodeid (str): The node id

    Returns:
        F: This is the function used to get the value
    """

    return F(f'{RESOURCE_MERGED_TILE_DATA_KEY}__{nodeid}')