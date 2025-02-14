from django.db.models import Func, F, ExpressionWrapper, FloatField, CharField
from typing import Dict, List
from arches.app.models.models import Node

def expression_string_datatype(nodeid: str, lang: str = 'en') -> ExpressionWrapper:
    return ExpressionWrapper(
        F(f'data__{nodeid}__{lang}__value'),
        output_field=CharField()
    )

# ! Doesn't have a datatype
def expression_number_datatype(nodeid: str) -> ExpressionWrapper:
    return ExpressionWrapper(
        F(f'data__{nodeid}'),
        output_field=FloatField()
    )