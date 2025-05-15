import re
from .config import (
    GREATER_THAN_KEYS, 
    LESS_THAN_KEYS, 
    GREATER_THAN_OR_EQUAL_KEYS, 
    LESS_THAN_OR_EQUAL_KEYS, 
    NOT_EQUAL_KEYS, 
    CONTAINS_KEYS, 
    INSENSITIVE_CONTAINS_KEYS,
    STARTS_WITH_KEYS,
    INSENSITIVE_STARTS_WITH_KEYS,
    ISNULL_KEYS
)
from typing import List, TYPE_CHECKING
from django.db.models import Q
from typing import TypedDict, Dict

if TYPE_CHECKING:
    from .query_builder import FilterStructure

class SplitQueryKeyReturn(TypedDict):
    field_key: str
    additional_keys: List[str]
    operator: str

def domain_value_annotation_key(node_alias: str):
    return f'{annotation_key(node_alias)}_domain_value'

def default_value_annotation_key(node_alias: str):
    return f'{annotation_key(node_alias)}_default'

def annotation_key(node_alias: str) -> str:
    """
    Method handles returning the annotation key. We are just keeping structure towards the annotation key

    Args:
        node_alias (str): The node alias for example age, person, name, etc.

    Returns:
        str: The transfromed string, this just appends '_annotation' on the node alias
    """
    return f'{node_alias}_annotation';

def handle_operatortion(raw_operator: str | None) -> str:
    """
    Method returns the appropriate operation key, if the key is contained within any const. If not then it returns 'equal' by default as remember in Django
    you cannot define equals within the key like age__gt

    Args:
        raw_operator (str | None): This is the operator which the user as typed in

    Returns:
        str: The appropriate operation key
    """
    if not raw_operator:
        return 'equal'
    
    if raw_operator in STARTS_WITH_KEYS:
        return 'startswith'
    
    if raw_operator in INSENSITIVE_STARTS_WITH_KEYS:
        return 'istartswith'
    
    if raw_operator in ISNULL_KEYS:
        return 'isnull'

    if raw_operator in INSENSITIVE_CONTAINS_KEYS:
        return 'icontains'
    
    if raw_operator in CONTAINS_KEYS:
        return 'contains'
    
    if raw_operator in GREATER_THAN_KEYS:
        return 'gt'
    
    if raw_operator in LESS_THAN_KEYS:
        return 'lt'
    
    if raw_operator in GREATER_THAN_OR_EQUAL_KEYS:
        return 'gte'
    
    if raw_operator in LESS_THAN_OR_EQUAL_KEYS:
        return 'lte'

    # * Need to handle this operator, needs meaning that this should be stored in a excludes, instead of filter
    if raw_operator in NOT_EQUAL_KEYS:
        return 'not_equal'
    
    return 'equal'
        

def transform_exclude_structure_towards_query(excludeStructure: List["ExcludeStructure"]) -> Q:
    """
    Method for transforming a filter structure towrads a query, basically the filter or exclude is structured in a way for the purpose towards this method.
    The reason being as before we had filter(**kwargs), however this could not handle OR & AND statement properly, therefore this method was developed.
    This method should take this structure and convert it to a Q object, stating ANDs & ORs so the return value for this method is compatlile with
    filter(transform_filter_exclude_structure_towards_query()) or exclude(transform_filter_exclude_structure_towards_query()), towards Django

    Args:
        structures (List[&quot;FilterStructure&quot;] | List["ExcludeStructure"]): This is the filter structure which is contained within query_builder.py and set within filters.py

    Returns:
        Q: This is the Query object return and suitable for filter() or exclude()
    """
    query: Q = Q()
    
    # * Loop through the filtered structures
    for structure in excludeStructure:
        # * Get the operators and filters from this structure
        operator = structure.get('logical_operator', 'AND')
        conditions = structure.get('conditions', {})
        
        # ? In Django, using .exclude() with a condition like field=value will exclude records where field equals value. 
        # ? However, if the field contains None (i.e., SQL NULL), these records are not returned by default when using .exclude().​
        # ? https://www.atlassian.com/data/databases/how-to-filter-for-empty-or-null-values-in-a-django-queryset 
        isnullconditions = {}
        for field, value in conditions.items():
            if value is not None:
                isnullconditions[f'{field}__isnull'] = False

        condition_query = Q(**isnullconditions, **conditions)
        
        # * Append & or | towards the query
        if operator.upper() == 'OR':
            query |= condition_query
        else:   
            query &= condition_query
    
    return query


def transform_filter_structure_towards_query(filter_structurers: List["FilterStructure"]) -> Q:
    """
    Methods job is to transfrom the filter structure from the query_builder.py and convert these structures into Django Q objects, therefore
    we can use these Q objects inside filter() or exclude()

    Args:
        structures (List[&quot;FilterStructure&quot;]): This is the filter structure which is contained within query_builder.py and set within filters.py

    Returns:
        Q: This is the Query object return and suitable for filter()
    """

    def _make_nested_none_or_null_q_objects(key: str, value: any) -> Q | None:
        """
        Stu noticed that if the tile nodegroup section wasn't created within the tiles data table, then __isnull would of worked but
        equals None didn't work. Also  if the tile nodegroup section was created within the tiles data table, then None would of worked
        but isnull didn't work. With this in mind, I created this method to help slove the problem, by simpley attaching a OR filtering/excluding
        query after, based on the query the user gave, therefore we checked for __isnull OR None. I also want to point out that some expressions
        handle progressing None values differently for example the DateFieldModel can sometimes produce a value 'null' for None or Null values

        Args:
            key (str): Key from the single condition
            value (any): Value from the single condition
        """
        parts = key.split("__")
        found_operator = parts[-1] if len(parts) > 1 else None

        def _make_all_none_queries(find_none: bool):

            q_list = Q()

            if find_none:
                q_list |= _make_nested_q_object(parts[0], None)
                q_list |= _make_nested_q_object(parts[0] + '__isnull', True)
                q_list |= _make_nested_q_object(parts[0], 'null')

            else:
                q_list |= _make_nested_q_object(parts[0] + '__not_equal', None)
                q_list |= _make_nested_q_object(parts[0] + '__isnull', False)
                q_list |= _make_nested_q_object(parts[0] + '__not_equal', 'null')

            return q_list
        
        if found_operator != None and found_operator == 'isnull':
            return _make_all_none_queries(True) if value else _make_all_none_queries(False)

        elif value == None:
            if (found_operator == None): return _make_all_none_queries(True)
            elif (found_operator in NOT_EQUAL_KEYS): return _make_all_none_queries(False)

        return None;

    def _make_nested_q_object(key, value) -> Q:
        """
        This method makes a single Q object from a single condition age=40. You can see that NOT_EQUALS is also handled in this section aswel
        for example age__not_equal=40

        Args:
            key (str): Key from the single condition
            value (any): Value from the single condition

        Returns:
            Q: The Q object from Django which is created
        """
        parts = key.split("__")
        found_operator = parts[-1] if len(parts) > 1 else None

        if found_operator in NOT_EQUAL_KEYS:
            return ~Q(**{key.replace("__not_equal", ""): value})
        else:
            return Q(**{key: value})  

    def _make_filter_conditions_q_objects(condition_logical_operator: str, conditions: Dict[str, any]) -> Q:
        """
        Method handles creating all conditions into Q objects from a single FilterStructure. 

        Args:
            condition_logical_operator (str): This can be either 'AND' or 'OR' but is for the conditions query for example where(height__gt=5, __or: {age=40, gender='Male'})
                so for age it's (height__gt *AND* (age=40 *OR* gender='Male'))
            conditions: These are the user inputs for example where(age=40, gender='Male') so age=40, gender='Male'

        Returns:
            Q: The Q object from Django which is created
        """
        filter_condition_query = Q()

        for key, value in conditions.items():
            # * This is checking if the value is a deep level condition using __or | __and keys
            if isinstance(value, dict) and "conditions" in value:
                nested_q = _make_filter_conditions_q_objects(
                    value.get("condition_logical_operator", "AND"),
                    value["conditions"]
                )

            # * This checks if the value is an array for example the user could enter a query like -> 'report_submitted_by_value': [None, 'null']
            elif isinstance(value, (list, tuple, set)):
                q_list = Q()
                for v in value:
                    sub_nested_q = _make_nested_none_or_null_q_objects(key, value)
                    q_list |=  _make_nested_q_object(key, v) if sub_nested_q == None else sub_nested_q
                nested_q = q_list

            # * Handles checking Null value but is the default option is the value is not an array or a FilterStructure
            else:
                nested_q = _make_nested_none_or_null_q_objects(key, value)
                if nested_q == None: nested_q = _make_nested_q_object(key, value)

            # * This section handles the filter condition query, if they should be an OR or an AND
            if condition_logical_operator.upper() == 'OR':
                filter_condition_query |= nested_q
            else:
                filter_condition_query &= nested_q

        return filter_condition_query

    def _make_filter_structurer_q_obects() -> Q:
        """
        Method handles making Q objects from filter structures

        Returns:
            Q: The Q object from Django which is created
        """
        filter_structurer_querys = Q()

        for filter_structurer in filter_structurers:
            # * Get values from the filter structure
            logical_operator = filter_structurer.get('logical_operator', 'AND')
            condition_logical_operator = filter_structurer.get('condition_logical_operator', 'AND')
            conditions = filter_structurer.get('conditions', {})

            # * Convert conditions over to Q objects
            condition_q = _make_filter_conditions_q_objects(condition_logical_operator, conditions)

            # * This section handles the filter structure query, if they should be an OR or an AND
            if logical_operator.upper() == 'OR':
                filter_structurer_querys |= condition_q
            else:
                filter_structurer_querys &= condition_q

        return filter_structurer_querys

    return _make_filter_structurer_q_obects()
    

def split_query_key(key: str) -> SplitQueryKeyReturn | None:
    """
    Method is used to the raw query key up for example where(first_name__en__contains='Aid'), this would return something like this
    field_key: 'first_name',
    additional_keys: ['en']
    operator: 'contains'

    Args:
        key (str): This is the raw key, from the above example this would be first_name__en__contains

    Returns:
        SplitQueryKeyReturn | None: Returns None if the key is invalid or returns the Dict
    """
    pattern = r"([a-zA-Z0-9__]+)"
    match = re.search(pattern, key)

    if not match:
        return None;

    found_values: List[str] = match.group(1).split('__')
    operator: str = handle_operatortion(found_values[-1]);

    # * Remove the last key from found values as this is the operator
    if (operator != 'equal'):
        found_values.pop();

    field_key: str = found_values[0]
    found_values.pop(0)
    additional_keys: List[str] = found_values;

    return {
        'field_key': field_key,
        'additional_keys': additional_keys,
        'operator': operator
    }