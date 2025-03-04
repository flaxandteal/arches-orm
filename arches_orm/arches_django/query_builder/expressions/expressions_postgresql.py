from django.db.models import Func, F, ExpressionWrapper, FloatField, CharField, DateTimeField, OuterRef, Subquery, BooleanField
from arches.app.models.models import Value as ValuesModel
from typing import Dict, List
from arches.app.models.models import Node
from django.db import connection
from datetime import datetime
from django.conf import settings

def _postgresql_expression_string_datatype(nodeid: str, addional_keys: List[str] = None) -> F:
    """
    Method gets the experssion for a string datatype. This is mainaly used for the tiles JSON column that is stored within the database so we can use
    annotations around the expressions

    Args:
        nodeid (str): The node id
        addional_keys (List[str], optional): The addional keys are used towards the user input for example firstname__en='Harry'. Defaults to None.

    Returns:
        F: This is the function used to get the value
    """

    key_lang = addional_keys[0] if len(addional_keys) >= 1 else 'en'
    value_lang = addional_keys[1] if len(addional_keys) >= 2 else 'value'

    return  F(f'data__{nodeid}__{key_lang}__{value_lang}')