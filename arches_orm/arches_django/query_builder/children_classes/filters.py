import re
from ..utilities import split_query_key, annotation_key, SplitQueryKeyReturn
from arches.app.models.models import Node
import uuid
from typing import TYPE_CHECKING, Dict, List
from arches_orm.arches_django.query_builder.config import NOT_EQUAL_KEYS
from arches_orm.arches_django.query_builder.annotations.annotations import set_annotation

class QueryBuilderFilters:
    _instance_query_builder = None;
    _wrapper_instance = None;

    _append_filters: List[any] = [];
    _append_excludes: List[any] = [];

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
            self._filters[field_key] = value

        elif field_lookup in NOT_EQUAL_KEYS:
            self._excludes[field_key] = value
        
        else:
            self._filters[field_key + "__" + field_lookup] = value

    def _reset_previous_filtering_excluding(self):
        """
        The data is retained as the query builder is uses a single ton towards this class 
        """
        self._filters = {}
        self._excludes = {}

        self._append_filters = []
        self._append_excludes = []

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

            if (query['field_key'] == 'resourceinstance' and len(query['additional_keys']) > 0):
                self._handle_setting_excludes_filters(query['field_key'], query['operator'], value)

            else:
                set_annotation(
                    self._instance_query_builder,
                    query['field_key'],
                    node,
                    query['additional_keys']
                )
                # * We do use the annotation_key as the filter field_key as within set_annotation it setups the annotation with the key as annotation_key(query['field_key'])
                # * and the value as the expression wrapper, therefore we have to use the same key to filter with
                self._handle_setting_excludes_filters(annotation_key(query['field_key']), query['operator'], value)
                
            self._handle_isnull_and_none_queries(query, value, node)

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
              
        if (self._append_filters != None): self._instance_query_builder._filter_structures.extend(self._append_filters)
        if (self._append_excludes != None): self._instance_query_builder._exclude_structures.extend(self._append_excludes)

    def _handle_isnull_and_none_queries(self, query: SplitQueryKeyReturn, value: any, node: Node):
        """
        Stu noticed that if the tile nodegroup section wasn't created within the tiles data table, then __isnull would of worked but
        equals None didn't work. Also  if the tile nodegroup section was created within the tiles data table, then None would of worked
        but isnull didn't work. With this in mind, I created this method to help slove the problem, by simpley attaching a OR filtering/excluding
        query after, based on the query the user gave, therefore we checked for __isnull OR None

        Args:
            query (SplitQueryKeyReturn): Current query
            value (any): Current value
        """

        def _append_fitler(logical_operator: str, conditions):
            """
            Method handles applying on lifecycle append filter

            Args:
                logical_operator (str): OR | AND, the operator
                conditions (_type_): {age=30}, the conditions
            """
            self._append_filters.append({ 'logical_operator': logical_operator, 'conditions': conditions })

        def _append_exclude(logical_operator: str, conditions):
            """
            Method handles applying on lifecycle append exclude

            Args:
                logical_operator (str): OR | AND, the operator
                conditions (_type_): {age=30}, the conditions
            """
            self._append_excludes.append({ 'logical_operator': logical_operator, 'conditions': conditions })

        def _run_callbacks(callbacks: dict, node_datatype: str):
            """
            Method handles running the callback methods once gained from the handlers. This should define callback methods towards 
            _append_filter & _append_exclude to give the complete None or Null values from the database. I've also defined node types
            as some expression causes issue but are needed for example the DateFieldModel is needed to use gt or lt on dates, however
            this model can transfrom the None or Null value into a string named 'null', hence the reason for this callback.

            Args:
                callbacks (dict): The selected callbacks from the handlers
                node_datatype (str): The node datatype selected
            """
            callbacks['default']();
            if (node_datatype in callbacks): callbacks[node_datatype]();

        handlers = {
            'isnull': {
                True: {
                    'default': lambda: _append_fitler('OR', { annotation_key(query['field_key']): None }),
                    'date': lambda: _append_fitler('OR', { annotation_key(query['field_key']): 'null' })
                },
                False: {
                    'default': lambda: _append_exclude('OR', { annotation_key(query['field_key']): None }),
                    'date': lambda: _append_exclude('OR', { annotation_key(query['field_key']): 'null' })
                }
            },
            'None': {
                'equal': {
                    'default': lambda: _append_fitler('OR', { annotation_key(query['field_key'] + '__isnull'): True }),
                    'date': lambda: _append_fitler('OR', { annotation_key(query['field_key']): 'null' })
                },
                'not_equal': {
                    'default': lambda: _append_fitler('OR', { annotation_key(query['field_key'] + '__isnull'): False }),
                    'date': lambda: _append_exclude('OR', { annotation_key(query['field_key']): 'null' })
                }
            }
        }

        callbacks = None;
        
        if query['operator'] == 'isnull':
            callbacks = handlers['isnull'][value]

        elif value == None and (query['operator'] == 'equal' or query['additional_keys'] == 'not_equal'):
            callbacks = handlers['None'][value]

        if (callbacks != None): _run_callbacks(callbacks, node.datatype)

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