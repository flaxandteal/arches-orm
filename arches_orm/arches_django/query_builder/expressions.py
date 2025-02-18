from django.db.models import Func, F, ExpressionWrapper, FloatField, CharField, Value, DateField
from typing import Dict, List
from arches.app.models.models import Node
from django.db import connection

# users = User.objects.annotate(fake_value=Value("FakeData", output_field=CharField()))


def expression_string_datatype(nodeid: str, addional_keys: List[str] = None) -> ExpressionWrapper:
    """
    Method gets the experssion for a string datatype. This is mainaly used for the tiles JSON column that is stored within the database so we can use
    annotations around the expressions

    Args:
        nodeid (str): The node id
        addional_keys (List[str], optional): The addional keys are used towards the user input for example firstname__en='Harry'. Defaults to None.

    Returns:
        ExpressionWrapper: This is the expression wrapper that is returned and should be mainly used for annotations
    """

    key_lang = addional_keys[0] if len(addional_keys) >= 1 else 'en'
    value_lang = addional_keys[1] if len(addional_keys) >= 2 else 'value'

    return ExpressionWrapper(
        F(f'data__{nodeid}__{key_lang}__{value_lang}'),
        output_field=CharField()
    )

def expression_date_datatype(nodeid: str) -> ExpressionWrapper:
 # Check the database vendor
    if connection.vendor == 'postgresql':
        # PostgreSQL - Use TO_DATE function
        return ExpressionWrapper(
            Func(F(f'data__{nodeid}'), function='TO_DATE', template="%(function)s(%(expressions)s, 'YYYY-MM-DD\"T\"HH24:MI:SS.MS\"TZ\"')"),
            output_field=DateField()
        )
    elif connection.vendor == 'sqlite':
        # SQLite - Use STRFTIME to extract date
        return ExpressionWrapper(
            Func(F(f'data__{nodeid}'), function='STRFTIME', template="%(function)s('%%Y-%%m-%%d', %(expressions)s)"),
            output_field=DateField()
        )
    else:
        # For other databases, you can implement default behavior or throw an error if unsupported
        raise NotImplementedError(f"Unsupported database vendor: {connection.vendor}")

def expression_number_datatype(nodeid: str) -> ExpressionWrapper:
    """
    Method gets the experssion for a number datatype. This is mainaly used for the tiles JSON column that is stored within the database so we can use
    annotations around the expressions

    Args:
        nodeid (str): The node id

    Returns:
        ExpressionWrapper: This is the expression wrapper that is returned and should be mainly used for annotations
    """
    return ExpressionWrapper(
        F(f'data__{nodeid}'),
        output_field=FloatField()
    )