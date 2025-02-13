import re
from arches.app.utils.permission_backend import get_nodegroups_by_perm

def annotation_key(node_alias: str):
    return f'{node_alias}_annotation';

def transform_query(input_string):
    # Match pattern for the string format, allowing additional keys
    operators = ['=', '=>', '=<', '<', '>']

    # Create a regex pattern that matches any of the operators
    pattern = r"([a-zA-Z0-9__]+)(" + "|".join(map(re.escape, operators)) + r")([^\s]+)"

    # Search for the key, operator, and value
    match = re.search(pattern, input_string)

    if not match:
        return None;

    keys = match.group(1).split('__')

    operator = match.group(2)
    value = match.group(3)
    key = keys[0]
    keys.pop(0)
    additional_keys = keys

    return {
        'key': key,
        'additional_keys': additional_keys,
        'operator': operator,
        'value': value
    }