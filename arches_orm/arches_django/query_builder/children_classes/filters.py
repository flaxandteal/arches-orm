import re
from ..utilities import split_query_key, annotation_key, SplitQueryKeyReturn
from arches.app.models.models import Node
import uuid
from typing import TYPE_CHECKING, Dict, List
from arches_orm.arches_django.query_builder.config import NOT_EQUAL_KEYS, OR_CONDITION_LOGICAL_OPERATOR, AND_CONDITION_LOGICAL_OPERATOR
from arches_orm.arches_django.query_builder.annotations.annotations import set_annotation

if TYPE_CHECKING:
    from ..query_builder import FilterStructure

class QueryBuilderFilters:
    _instance_query_builder = None;
    _wrapper_instance = None;

    _nodes = {};

    if TYPE_CHECKING:
        from arches_orm.arches_django.query_builder.query_builder import QueryBuilder

    def __init__(self, instance_query_builder):
        self._instance_query_builder = instance_query_builder;
        self._wrapper_instance = instance_query_builder._parent_wrapper_instance;

    def _transform_filter_field_key(self, field_key: str, field_lookup: str) -> str:
        """
        Method just handles the field key transfrom for the filter so we do something like this filter(age__gt=30)

        Args:
            field_key (str): key, age
            field_lookup (str): field lookup, gt

        Returns:
            str: The field key transformed
        """

        if field_lookup == 'equal':
            return field_key;

        return field_key + "__" + field_lookup

    def _create_filter_structurer(self, logical_operator: str, condition_logical_operator: str, **kwargs) -> "FilterStructure":
        """
        Method handles creating the structure for the filter structure from the users input and calls _create_filter_conditions for the 
        conditions

        Args:
            logical_operator (str): This can be either 'AND' or 'OR' but is for the parent query for example where(age=40, gender='Male').or_where(firstname='Ben')
                so it's *AND* ((age=40, gender='Male')) *OR* (firstname='Ben') 
            condition_logical_operator (str): This can be either 'AND' or 'OR' but is for the conditions query for example where(height__gt=5, __or: {age=40, gender='Male'})
                so for age it's (height__gt *AND* (age=40 *OR* gender='Male'))
            kwargs: These are the user inputs for example where(age=40, gender='Male') so age=40, gender='Male'

        Returns:
            FilterStructure: Returns the filter structure and has the annotations setup within the query_builder.py
        """
        return {
            'logical_operator': logical_operator,
            'condition_logical_operator': condition_logical_operator,
            'conditions': self._create_filter_conditions(**kwargs)
        }

    def _create_filter_conditions(self, **kwargs) -> Dict[str, any]:
        """
        Method handles setting up the conditions for the filter inside a filter structure/structurer. Simple we setup annotations and get the
        appoirate Django query key as we have custom keys for example ISNULL_KEYS = ['isnull', 'isnone'], however in Django it's just 'isnull'

        Args:
            kwargs: These are the user inputs for example where(age=40, gender='Male') so age=40, gender='Male'

        Raises:
            ValueError: If the node_alias doesn't exist within nodes, the Error is raised

        Returns:
            Dict[str, any]: Returns the conditions for the filter inside a filter structure/structurer
        """
        filters_conditions = {}

        for key, value in kwargs.items():
            if key in OR_CONDITION_LOGICAL_OPERATOR:
                # ? Adding a custom UUID allows for more __or within the same filter condition as the object is a dict and having only __or might
                # ? override the previous __or
                custom_uuid = uuid.uuid4()
                filters_conditions[str(custom_uuid) + key] = self._create_filter_structurer(logical_operator='AND', condition_logical_operator='OR', **value)
                continue;

            if key in AND_CONDITION_LOGICAL_OPERATOR:
                # ? Adding a custom UUID allows for more __or within the same filter condition as the object is a dict and having only __and might
                # ? override the previous __and
                custom_uuid = uuid.uuid4()
                filters_conditions[str(custom_uuid) + key] = self._create_filter_structurer(logical_operator='AND', condition_logical_operator='AND', **value)
                continue;

            # * We split the key query down as they might be addional information or different operation handling needed
            query = split_query_key(key)
            node: Node = self._nodes.get(query['field_key'])

            if node == None:
                raise ValueError('Node is not found with alias ' + query['field_key'])

            # * Here we check if the user is trying to access the resourceinstance as we don't want to apply any custom annotation since
            # * within our query is .selected_related('resourceinstance'). The user can access this aswel
            if (query['field_key'] == 'resourceinstance' and len(query['additional_keys']) > 0):
                field_key = self._transform_filter_field_key(query['field_key'], query['operator'])

            # * Default, we setup the annotation for the field and add the field onto filters_conditions
            else:
                set_annotation(
                    self._instance_query_builder,
                    query['field_key'],
                    node,
                    query['additional_keys']
                )
                # * We do use the annotation_key as the filter field_key as within set_annotation it setups the annotation with the key as annotation_key(query['field_key'])
                # * and the value as the expression wrapper, therefore we have to use the same key to filter with
                field_key = self._transform_filter_field_key(annotation_key(query['field_key']), query['operator'])

            filters_conditions[field_key] = value;

        return filters_conditions;

    def where(self, **kwargs) -> "QueryBuilder":
        """
        This method calls the _where_core, however this is strictly only for AND logical operations

        Returns:
            QueryBuilder: This is the query builder instance and this is return for the reason of Chainable
        """
        
        self._nodes: List[Node] = self._wrapper_instance._node_objects_by_alias();
        
        filter_structurer = self._create_filter_structurer(logical_operator='AND', condition_logical_operator='AND', **kwargs);
        self._instance_query_builder._filter_structures.append(filter_structurer)

        return self._instance_query_builder;

    def or_where(self, **kwargs) -> "QueryBuilder":
        """
        This method calls the _where_core, however this is strictly only for OR logical operations

        Returns:
            QueryBuilder: This is the query builder instance and this is return for the reason of Chainable
        """
        self._nodes: List[Node] = self._wrapper_instance._node_objects_by_alias();

        filter_structurer = self._create_filter_structurer(logical_operator='OR', condition_logical_operator='AND', **kwargs);
        self._instance_query_builder._filter_structures.append(filter_structurer)

        return self._instance_query_builder;    