from django.db.models import Func, F, ExpressionWrapper, FloatField, CharField, DateTimeField, OuterRef, Subquery, BooleanField, JSONField,  Case, Value, When
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
from arches_orm.arches_django.query_builder.utilities import domain_value_annotation_key
from .expressions import ExpressionDomainValueReturnType

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

def postgresql_expression_domain_value(node: Node, addional_keys: List[str] = None) -> ExpressionDomainValueReturnType:
    key_lang = addional_keys[0] if addional_keys and len(addional_keys) >= 1 else 'en'
    options = node.config.get('options', [])
    dynamic_annotation_key = domain_value_annotation_key(node.alias)

    when_conditions = []
    for option in options:
        node_id = option.get("id")
        selected_option = option['text'][key_lang]

        when_conditions.append(
            When(**{dynamic_annotation_key: node_id}, then=Value(selected_option))
        )

    case_expression = Case(*when_conditions, default=Value(None))

    # ! Unfortually, When() as some issues with running database functions as conditions, therefore we use default to extract the domain value id
    # ! and then use this default key as the condition to check which node option it is paired with
    return {
        "default": F(f'{RESOURCE_MERGED_TILE_DATA_KEY}__{node.nodeid}'),
        "annotation": ExpressionWrapper(
            case_expression,
            output_field=CharField()
        )
    }