import re






allowed_operators_datatypes = {
    'where': {
        '=': {
            'string': _handle_datatype_string
        }
    }
}

def where(*args):
    
    for index in range(len(args)):
    
        query = split_filter_string(args[index])

        print(query)

    return;

def where_in():
    return;

def split_filter_string(input_string):
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