from django.db.models import F, ExpressionWrapper, IntegerField
from django.db.models import Func, F, ExpressionWrapper, IntegerField, CharField

def annotation_string_datatype(nodeid: str):
    # ! Not sure how to apporoach this
    default_lang = 'en'

    return ExpressionWrapper(
        F(f'data__{nodeid}__{default_lang}__value'),
        output_field=CharField()
    )