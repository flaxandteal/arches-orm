from tests.utilities.common import create_tile_from_model
from tests.utilities.seeders.common import (
    number_seeder_odd_even, 
    date_seeder_50_50_precent_older_future_dates_from_present, 
    boolean_seeder_50_50_false_true,
    date_seeder_33_precent_present_past_future_dates_from_present
)
from datetime import datetime
import random
from datetime import datetime, timedelta
from django.utils.timezone import now
from arches_orm.arches_django.query_builder.config import (
    GREATER_THAN_KEYS,
    LESS_THAN_KEYS,
    LESS_THAN_OR_EQUAL_KEYS,
    GREATER_THAN_OR_EQUAL_KEYS,
    NOT_EQUAL_KEYS,
    CONTAINS_KEYS,
    INSENSITIVE_CONTAINS_KEYS
)

from django.db.models import F, BooleanField, ExpressionWrapper
from tests.utilities.seeders.seeder import Seeder
from tests.utilities.seeders.default.config import (
    PERSON_DATATYPE_NODE_ALIAS_KEYS, 
    ACTIVITY_DATATYPE_NODE_ALIAS_KEYS, 
    PERSON_DEFAULT_SEED_PATH, 
    ACTIVITY_DEFAULT_SEED_PATH
)
from arches.app.models.models import TileModel

def sub_test_filter_where(arches_orm):
    instance_arches_orm_model_activity = arches_orm.models.Activity
    instance_activity_seeder = Seeder(instance_arches_orm_model_activity, ACTIVITY_DATATYPE_NODE_ALIAS_KEYS, ACTIVITY_DEFAULT_SEED_PATH)

    instance_arches_orm_model_person = arches_orm.models.Person
    instance_person_seeder = Seeder(instance_arches_orm_model_person, PERSON_DATATYPE_NODE_ALIAS_KEYS, PERSON_DEFAULT_SEED_PATH)

    # sub_test_filter_where_concept_quries(instance_arches_orm_model_activity, instance_activity_seeder)
    sub_test_filter_where_boolean_quries(instance_arches_orm_model_person, instance_person_seeder)
    sub_test_filter_where_date_quries(instance_arches_orm_model_person, instance_person_seeder)
    sub_test_filter_where_number_quries(instance_arches_orm_model_person, instance_person_seeder)
    sub_test_filter_where_string_quries(instance_arches_orm_model_person, instance_person_seeder)


def sub_test_filter_where_boolean_quries(instance_arches_orm_model_person, instance_person_seeder):
    target_node_alias = PERSON_DATATYPE_NODE_ALIAS_KEYS['boolean'][-1];

    def _equal():
        nonlocal target_node_alias

        instance_person_seeder.seed(6, { 'boolean': boolean_seeder_50_50_false_true })
        true_records = instance_arches_orm_model_person.where(**{f"{target_node_alias}": True }).get()
        false_records = instance_arches_orm_model_person.where(**{f"{target_node_alias}": False }).get()

        for true_record in true_records:
            assert(instance_person_seeder.get_nested_datatype_value(true_record, 'boolean') == True)

        for false_record in false_records:
            assert(instance_person_seeder.get_nested_datatype_value(false_record, 'boolean') == False)

    _equal()
    _equal()
    _equal()

def sub_test_filter_where_date_quries(instance_arches_orm_model_person, instance_person_seeder):
    target_node_alias = PERSON_DATATYPE_NODE_ALIAS_KEYS['date'][-1];
    today_date = now().date()

    def _convert_date_string_date_object(date_str: str):
        return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S%z").date()


    def _greater_than():
        instance_person_seeder.seed(4, { 'date': date_seeder_50_50_precent_older_future_dates_from_present })
        operator = random.choice(GREATER_THAN_KEYS)
        records = instance_arches_orm_model_person.where(**{f"{target_node_alias}__{operator}": today_date }).get()

        for record in records:
            date_obj = _convert_date_string_date_object(str(instance_person_seeder.get_nested_datatype_value(record, 'date')))
            assert(date_obj > today_date)

    def _greater_than_or_equal():
        instance_person_seeder.seed(4, { 'date': date_seeder_33_precent_present_past_future_dates_from_present })
        operator = random.choice(GREATER_THAN_OR_EQUAL_KEYS)
        records = instance_arches_orm_model_person.where(**{f"{target_node_alias}__{operator}": today_date }).get()

        for record in records:
            date_obj = _convert_date_string_date_object(str(instance_person_seeder.get_nested_datatype_value(record, 'date')))
            assert(date_obj >= today_date)

    def _less_than():
        instance_person_seeder.seed(4, { 'date': date_seeder_50_50_precent_older_future_dates_from_present })
        operator = random.choice(LESS_THAN_KEYS)
        records = instance_arches_orm_model_person.where(**{f"{target_node_alias}__{operator}": today_date }).get()

        for record in records:
            date_obj = _convert_date_string_date_object(str(instance_person_seeder.get_nested_datatype_value(record, 'date')))
            assert(date_obj < today_date)

    def _less_than_or_equal():
        instance_person_seeder.seed(4, { 'date': date_seeder_33_precent_present_past_future_dates_from_present })
        operator = random.choice(LESS_THAN_OR_EQUAL_KEYS)
        records = instance_arches_orm_model_person.where(**{f"{target_node_alias}__{operator}": today_date }).get()

        for record in records:
            date_obj = _convert_date_string_date_object(str(instance_person_seeder.get_nested_datatype_value(record, 'date')))
            assert(date_obj <= today_date)

    # ! BLOCKED DOING EQUAL AND NOT EQUALS FOR NOW
    # def _equal():
    #     instance_person_seeder.seed(3, { 'date': date_seeder_33_precent_present_past_future_dates_from_present })
    #     records = instance_arches_orm_model_person.where(**{f"{target_node_alias}": today_date }).get()

    #     for record in records:
    #         date_obj = _convert_date_string_date_object(str(instance_person_seeder.get_nested_datatype_value(record, 'date')))
    #         print(date_obj)
    #         print(today_date)
    #         assert(date_obj == today_date)

    # def _not_equals():
    #     instance_person_seeder.seed(4, { 'date': date_seeder_33_precent_present_past_future_dates_from_present })
    #     operator = random.choice(LESS_THAN_OR_EQUAL_KEYS)
    #     records = instance_arches_orm_model_person.where(**{f"{target_node_alias}__{operator}": today_date }).get()

    #     for record in records:
    #         date_obj = _convert_date_string_date_object(str(instance_person_seeder.get_nested_datatype_value(record, 'date')))
    #         assert(date_obj <= today_date)

    _greater_than()
    _greater_than()
    _greater_than()

    _greater_than_or_equal()
    _greater_than_or_equal()
    _greater_than_or_equal()

    _less_than()
    _less_than()
    _less_than()

    _less_than_or_equal()
    _less_than_or_equal()
    _less_than_or_equal()

    # _equal()
    # _equal()
    # _equal()

    # _not_equals(63)
    # _not_equals(97)
    # _not_equals(43)

def sub_test_filter_where_concept_quries(instance_arches_orm_model_activity, instance_activity_seeder):
    activity = instance_arches_orm_model_activity.create()
    record_status = activity.record_status_assignment.record_status
    CollectionEnum = record_status.__collection__
    target_node_alias = ACTIVITY_DATATYPE_NODE_ALIAS_KEYS['concept'][-1];

    def concept_seed(index: int = None):
        import random
        nonlocal CollectionEnum
        return random.choice(list(CollectionEnum))
    
    def _equal():
        nonlocal concept_seed
        instance_activity_seeder.seed(4, { 'concept': concept_seed })
        concept_selected = concept_seed()
        search_value = concept_selected.value
        records = instance_arches_orm_model_activity.where(**{f"{target_node_alias}": 'Active - Full/Published' }).get()

        for record in records:
            assert(instance_activity_seeder.get_nested_datatype_value(record, 'concept') == 'Active - Full/Published')

    _equal();


def sub_test_filter_where_string_quries(instance_arches_orm_model_person, instance_person_seeder):

    instance_person_seeder.seed(10, { 'string': None })
    target_node_alias = PERSON_DATATYPE_NODE_ALIAS_KEYS['string'][-1];

    def _equal(value: str = 'parker'):
        instance_person_seeder.seed(3, { 'string': value })
        records = instance_arches_orm_model_person.where(**{f"{target_node_alias}": value}).get()

        for record in records:
            assert(instance_person_seeder.get_nested_datatype_value(record, 'string') == value)

    def _not_equals(value: str = 'parker'):
        instance_person_seeder.seed(3, { 'string': value })
        operator = random.choice(NOT_EQUAL_KEYS)
        records = instance_arches_orm_model_person.where(**{f"{target_node_alias}__{operator}": value}).get()

        for record in records:
            assert(instance_person_seeder.get_nested_datatype_value(record, 'string') != value)

    def _contains(value: str = 'parker'):
        sub_string = value[:(len(value) // 2)]
        instance_person_seeder.seed(3, { 'string': value })
        operator = random.choice(CONTAINS_KEYS)
        records = instance_arches_orm_model_person.where(**{f"{target_node_alias}__{operator}": sub_string}).get()

        for record in records:
            assert(sub_string in instance_person_seeder.get_nested_datatype_value(record, 'string'))

    def _insensitive_contains(value: str = 'parker'):
        sub_string = (value[:(len(value) // 2)]).upper()
        instance_person_seeder.seed(3, { 'string': value })
        operator = random.choice(INSENSITIVE_CONTAINS_KEYS)
        records = instance_arches_orm_model_person.where(**{f"{target_node_alias}__{operator}": sub_string}).get()

        for record in records:
            assert(sub_string.lower() in instance_person_seeder.get_nested_datatype_value(record, 'string').lower())

    _equal('sam')
    _equal('steve')
    _equal('john')

    _not_equals('mike')
    _not_equals('ben')
    _not_equals('pat')

    _contains('Bannanas in hats')
    _contains('Testing if this works')
    _contains('Dogs and cats')

    _insensitive_contains('bannanas in hats')
    _insensitive_contains('testing if this works')
    _insensitive_contains('dogs and cats')

def sub_test_filter_where_number_quries(instance_arches_orm_model_person, instance_person_seeder):
    instance_person_seeder.seed(10, { 'number': None })
    target_node_alias = PERSON_DATATYPE_NODE_ALIAS_KEYS['number'][-1];

    def _greater_than(value: int = 50):
        operator = random.choice(GREATER_THAN_KEYS)
        records = instance_arches_orm_model_person.where(**{f"{target_node_alias}__{operator}": value}).get()
        for record in records:
            assert(instance_person_seeder.get_nested_datatype_value(record, 'number') > value)

    def _less_than(value: int = 50):
        operator = random.choice(LESS_THAN_KEYS)
        records = instance_arches_orm_model_person.where(**{f"{target_node_alias}__{operator}": value}).get()
        for record in records:
            assert(instance_person_seeder.get_nested_datatype_value(record, 'number') < value)

    def _less_than_or_equal(value: int = 50):
        operator = random.choice(LESS_THAN_OR_EQUAL_KEYS)
        records = instance_arches_orm_model_person.where(**{f"{target_node_alias}__{operator}": value}).get()
        for record in records:
            assert(instance_person_seeder.get_nested_datatype_value(record, 'number') <= value)

    def _greater_than_or_equal(value: int = 50):
        operator = random.choice(GREATER_THAN_OR_EQUAL_KEYS)
        records = instance_arches_orm_model_person.where(**{f"{target_node_alias}__{operator}": value}).get()
        for record in records:
            assert(instance_person_seeder.get_nested_datatype_value(record, 'number') >= value)

    def _equal(value: int = 23):
        instance_person_seeder.seed(3, { 'number': value })
        records = instance_arches_orm_model_person.where(**{f"{target_node_alias}": value}).get()
        for record in records:
            assert(instance_person_seeder.get_nested_datatype_value(record, 'number') == value)

    def _not_equals(value: int = 23):
        instance_person_seeder.seed(3, { 'number': value })
        operator = random.choice(NOT_EQUAL_KEYS)
        records = instance_arches_orm_model_person.where(**{f"{target_node_alias}__{operator}": value}).get()

        for record in records:
            assert(instance_person_seeder.get_nested_datatype_value(record, 'number') != value)

    _greater_than(30)
    _greater_than(70)
    _greater_than(20)

    _less_than(5)
    _less_than(10)
    _less_than(5)

    _less_than_or_equal(53)
    _less_than_or_equal(12)
    _less_than_or_equal(64)

    _greater_than_or_equal(75)
    _greater_than_or_equal(12)
    _greater_than_or_equal(54)

    _equal(53)
    _equal(12)
    _equal(64)

    _not_equals(63)
    _not_equals(97)
    _not_equals(43)