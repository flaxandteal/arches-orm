import re
from arches.app.utils.permission_backend import get_nodegroups_by_perm
from .consts import GREATER_THAN_KEYS, LESS_THAN_KEYS, GREATER_THAN_OR_EQUAL_KEYS, LESS_THAN_OR_EQUAL_KEYS, NOT_EQUAL_KEYS, VALUE_EXIST_KEYS, VALUE_NON_EXIST_KEYS, CONTAINS_KEYS, INSENSITIVE_CONTAINS_KEYS
from typing import List, TYPE_CHECKING
from django.db.models import Q
from typing import TypedDict

if TYPE_CHECKING:
    from .query_builder import FilterStructure

class SplitQueryKeyReturn(TypedDict):
    field_key: str
    additional_keys: List[str]
    operator: str

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
    
    # * Need to handle this operator, needs meaning that this should be stored in a excludes, instead of filter using None
    if raw_operator in VALUE_EXIST_KEYS:
        return 'value_exist'
    
    # * Need to handle this operator, needs to with filter to search for None
    if raw_operator in VALUE_NON_EXIST_KEYS:
        return 'value_non_exist'
    
    return 'equal'
        

def transform_filter_structure_towards_query(filter_structures: List["FilterStructure"]) -> Q:
    """
    Method for transforming a filter structure towrads a query, basically the filter is structured in a way for the purpose towards this method.
    The reason being as before we had filter(**kwargs), however this could not handle OR & AND statement properly, therefore this method was developed.
    This method should take this filter structure and convert it to a Q object, stating ANDs & ORs so the return value for this method is compatlile with
    filter(transform_filter_structure_towards_query()), towards Django

    Args:
        filter_structures (List[&quot;FilterStructure&quot;]): This is the filter structure which is contained within query_builder.py and set within filters.py

    Returns:
        Q: This is the Query object return and suitable for filter()
    """
    query: Q = Q()
    
    # * Loop through the filtered structures
    for filter_structure in filter_structures:
        # * Get the operators and filters from this structure
        operator = filter_structure.get('logical_operator', 'AND')
        filters = filter_structure.get('filters', {})
        
        condition_query = Q(**filters)
        
        # * Append & or | towards the query
        if operator.upper() == 'OR':
            query |= condition_query
        else:   
            query &= condition_query
    
    return query

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