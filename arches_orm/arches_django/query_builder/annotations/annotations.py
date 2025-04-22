from ..utilities import annotation_key
from arches.app.models.models import Node
from typing import List, Dict
from django.db.models import F, Func, ExpressionWrapper, CharField, JSONField, Value
from arches_orm.arches_django.query_builder.utilities import domain_value_annotation_key

from .expressions.expressions import (
    expression_string_datatype, 
    expression_number_datatype, 
    expression_date_datatype, 
    expression_concept_value, 
    expression_domain_value,
    expression_boolean_value,
    expression_resource_instance_list_datatype, 
    expression_generic_default_fallback,
    expresion_merge_tile_json_data
)


def annotation_resource_merge_tile_data(current_database_engine: str) -> Dict[str, ExpressionWrapper | F]: 
    return expresion_merge_tile_json_data(current_database_engine)

def set_annotation(
    query_builder_instance,
    node_alias: str, 
    node: Node,
    addiontal_keys: List[str] = None 
):
    """
    Method adds a annoitation to the _annotations variable, if its not already contained. This gets the expressions by using the methods inside
    expressions.py for each datatype class. Then this _annotations variable is used within the selectors

    Args:
        key (str): The node alias
        node (Node): The node
        addiontal_keys (List[str], optional): Addional keys allowed for example firstname__en__value='Harry'
    """

    current_database_engine = query_builder_instance.database_engine

    if (node_alias in query_builder_instance._annotations):
        return;

    if (node.datatype == 'string'):
        query_builder_instance._annotations[annotation_key(node_alias)] = expression_string_datatype(current_database_engine, node.nodeid, addiontal_keys)

    elif (node.datatype == 'number'):
        query_builder_instance._annotations[annotation_key(node_alias)] = expression_number_datatype(current_database_engine, node.nodeid)

    elif (node.datatype == 'date'):
        query_builder_instance._annotations[annotation_key(node_alias)] = expression_date_datatype(node.nodeid)

    elif (node.datatype == 'boolean'):
            query_builder_instance._annotations[annotation_key(node_alias)] = expression_boolean_value(node.nodeid)

    elif (node.datatype == 'concept'):
        query_builder_instance._annotations[annotation_key(node_alias)] = expression_concept_value(node)

    elif (node.datatype == 'resource-instance-list'):
        query_builder_instance._annotations[annotation_key(node_alias)] = expression_resource_instance_list_datatype(current_database_engine, node.nodeid)

    elif (node.datatype == 'domain-value'):
        expressions = expression_domain_value(current_database_engine, node, addiontal_keys)

        query_builder_instance._before_annotations[domain_value_annotation_key(node_alias)] = expressions["default"]
        query_builder_instance._annotations[annotation_key(node_alias)] = expressions["annotation"]

    else:
        query_builder_instance._annotations[annotation_key(node_alias)] = expression_generic_default_fallback(current_database_engine, node.nodeid)