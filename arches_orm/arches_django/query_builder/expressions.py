from django.db.models import Func, F, ExpressionWrapper, FloatField, CharField, DateTimeField, OuterRef, Subquery, BooleanField
from arches.app.models.models import Value as ValuesModel
from typing import Dict, List
from arches.app.models.models import Node
from django.db import connection
from datetime import datetime

# users = User.objects.annotate(fake_value=Value("FakeData", output_field=CharField()))

def _figure_out_field_instance_type(value: str):
    try:
        datetime.fromisoformat(value)
        return DateTimeField
    except:
        pass
    
    try:
        int(value)
        return FloatField
    except:
        pass

    return CharField

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


def expression_boolean_value(nodeid: str) -> ExpressionWrapper:
    return ExpressionWrapper(
        F(f'data__{nodeid}'),
        output_field=BooleanField()
    )

def expression_domain_value(node: Node, addional_keys: List[str] = None) -> ExpressionWrapper:
    print(node.config.get("dateFormat"))
    key_lang = addional_keys[0] if len(addional_keys) >= 1 else 'en'
    value_lang = addional_keys[1] if len(addional_keys) >= 2 else 'value'

def expression_date_datatype(nodeid: str) -> ExpressionWrapper:
    """
    Converts a string-based date stored in `data__{nodeid}` into a proper DateTimeField 
    for sorting, based on the database backend.
    """
    return ExpressionWrapper(
        F(f'data__{nodeid}'),
        output_field=DateTimeField()
    )

def custom_test(value):
    print('HERE IS THE VALUE INSIDE CUSTOM TEST: ', value);
    return value;

def expression_concept_value(node: Node):
    from arches.app.models.concept import Concept

    concept_id = node.config.get('rdmCollection')
    print('ABOVE : ', ValuesModel.objects.filter(concept_id=concept_id))
    # print('INSIDE NODE ID : ', node.nodeid)    
    # collection = Concept().get(id=)

    return ExpressionWrapper(
        Subquery(
            ValuesModel.objects.filter(valueid=OuterRef(f'data__{node.nodeid}')).values('value')[:1]
        ),
        output_field=CharField()
    )

    # _figure_out_field_instance_type()

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