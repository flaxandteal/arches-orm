import re
from ..utilities import split_query_key, annotation_key
from django.db.models import Func, F, ExpressionWrapper, IntegerField, CharField
from arches.app.models.models import ResourceXResource, Node, NodeGroup, Edge, TileModel
import uuid
from typing import TYPE_CHECKING, List

class QueryBuilderFilters:
    _instance_query_builder = None;
    _wrapper_instance = None;

    if TYPE_CHECKING:
        from arches_orm.arches_django.query_builder.query_builder import QueryBuilder

    def __init__(self, instance_query_builder):
        self._instance_query_builder = instance_query_builder;
        self._wrapper_instance = instance_query_builder._parent_wrapper_instance;

    def _where_core(self, logical_operator: str, **kwargs):
        """
        Method handles the core of where towards where and or_where. The purpose of this method is to add a filter structure towards our 
        query builders filter structure to enable future filtering within selectors.py

        Args:
            logical_operator (str): This is the logical operator and should only be 'AND' | 'OR'
        """
        # * We need to get the nodes as we have to find the correct node towards the field key and then this node is used to find the datatype towards
        # * annotation
        nodes: List[Node] = self._wrapper_instance._node_objects_by_alias();
        filters: List[str, any] = {};

        # * Loop through keyword argmunets, this will be what the user has inputed for example where(age__gt=18)
        for key, value in kwargs.items():
            
            # * We split the key query down as they might be addional information or different operation handling needed
            query = split_query_key(key)
            node: Node = nodes.get(query['field_key'])

            self._instance_query_builder.set_annotation(
                key, 
                node
            )

            # * We do use the annotation_key as the filter field_key as within set_annotation it setups the annotation with the key as annotation_key(query['field_key'])
            # * and the value as the expression wrapper, therefore we have to use the same key to filter with
            if (query['operator'] == 'equal'):
                filters[annotation_key(query['field_key'])] = value

        # * Attach the filters and the logical operator (AND | OR) to the parent query builder for future use within selectors.py
        self._instance_query_builder._filter_structures.append({
            'logical_operator': logical_operator,
            'filters': filters
        })

    def where(self, **kwargs) -> "QueryBuilder":
        """
        This method calls the _where_core, however this is strictly only for AND logical operations

        Returns:
            QueryBuilder: This is the query builder instance and this is return for the reason of Chainable
        """
        self._where_core(logical_operator='AND', **kwargs);
        return self._instance_query_builder;

    def or_where(self, **kwargs) -> "QueryBuilder":
        """
        This method calls the _where_core, however this is strictly only for OR logical operations

        Returns:
            QueryBuilder: This is the query builder instance and this is return for the reason of Chainable
        """
        self._where_core(logical_operator='OR', **kwargs);
        return self._instance_query_builder;    