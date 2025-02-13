from django.db.models import F, ExpressionWrapper, IntegerField
from django.db.models import Func, F, ExpressionWrapper, IntegerField, CharField
from typing import Dict, List
from arches.app.models.models import Node

def expression_string_datatype(nodeid: str):
    # ! Not sure how to apporoach this
    default_lang = 'en'

    return ExpressionWrapper(
        F(f'data__{nodeid}__{default_lang}__value'),
        output_field=CharField()
    )

# ! Doesn't have a datatype
def expression_number_datatype(nodeid: str):
    return ExpressionWrapper(
        F(f'data__{nodeid}'),
        output_field=IntegerField()
    )