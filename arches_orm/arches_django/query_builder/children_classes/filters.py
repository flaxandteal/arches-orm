import re
from ..utilities import split_query_key, annotation_key
from arches.app.models.models import Node
import uuid
from typing import TYPE_CHECKING, Dict, List
from arches_orm.arches_django.query_builder.config import NOT_EQUAL_KEYS
from arches_orm.arches_django.query_builder.annotations.annotations import set_annotation

class QueryBuilderFilters:
    _instance_query_builder = None;
    _wrapper_instance = None;

    _filters: Dict[str, any] = {};
    _excludes: Dict[str, any] = {};

    if TYPE_CHECKING:
        from arches_orm.arches_django.query_builder.query_builder import QueryBuilder

    def __init__(self, instance_query_builder):
        self._instance_query_builder = instance_query_builder;
        self._wrapper_instance = instance_query_builder._parent_wrapper_instance;

    def _handle_setting_excludes_filters(self, field_key: str, field_lookup: str, value: any):
        """
        This method handles getting the correct filter key towards Django as we can have custom keys, that are defined in consts.py which point to the
        django key for example ['less_than']: 'lt'. This method gets the field key with the potational operator and stores this either in filters or excludes

        Args:
            field_key (str): The field key or node alias for example age
            field_lookup (str): The field key which was gained from the method "handle_operatortion"
            value (any): The value which the user inputted as the condition
        """

        if field_lookup == 'equal':
            self._filters[annotation_key(field_key)] = value

        elif field_lookup in NOT_EQUAL_KEYS:
            self._excludes[annotation_key(field_key)] = value
        
        else:
            self._filters[annotation_key(field_key) + "__" + field_lookup] = value

    def _reset_previous_filtering_excluding(self):
        """
        The data is retained as the query builder is uses a single ton towards this class 
        """
        self._filters = {}
        self._excludes = {}

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

        self._reset_previous_filtering_excluding()

        # * Loop through keyword argmunets, this will be what the user has inputed for example where(age__gt=18)
        for key, value in kwargs.items():
            
            # * We split the key query down as they might be addional information or different operation handling needed
            query = split_query_key(key)
            node: Node = nodes.get(query['field_key'])

            set_annotation(
                self._instance_query_builder,
                query['field_key'],
                node,
                query['additional_keys']
            )

            # * We do use the annotation_key as the filter field_key as within set_annotation it setups the annotation with the key as annotation_key(query['field_key'])
            # * and the value as the expression wrapper, therefore we have to use the same key to filter with
            self._handle_setting_excludes_filters(query['field_key'], query['operator'], value)

        # * Attach the filters and the logical operator (AND | OR) to the parent query builder for future use within selectors.py
        if self._filters:
            self._instance_query_builder._filter_structures.append({
                'logical_operator': logical_operator,
                'conditions': self._filters
            })

        if self._excludes:
              self._instance_query_builder._exclude_structures.append({
                'logical_operator': logical_operator,
                'conditions': self._excludes
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