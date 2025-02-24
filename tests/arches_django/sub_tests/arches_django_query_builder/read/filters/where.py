from tests.utilities.common import create_tile_from_model
from tests.utilities.seeders.default.person import person_seeder, get_nested_datatype_value, person_datatype_node_alias_keys
from tests.utilities.seeders.common import number_seeder_odd_even, date_seeder_50_50_precent_older_future_dates_from_present
from datetime import datetime
import random
from datetime import datetime, timedelta
from django.utils.timezone import now
from arches_orm.arches_django.query_builder.consts import (
    GREATER_THAN_KEYS,
    LESS_THAN_KEYS,
    LESS_THAN_OR_EQUAL_KEYS,
    GREATER_THAN_OR_EQUAL_KEYS,
    NOT_EQUAL_KEYS,
    CONTAINS_KEYS,
    INSENSITIVE_CONTAINS_KEYS
)
def sub_test_filter_where(arches_orm):
    # sub_test_filter_where_number_equal(arches_orm)
    sub_test_filter_where_number_quries(arches_orm)
    sub_test_filter_where_string_quries(arches_orm)

def sub_test_filter_where_string_quries(arches_orm):
    Person = arches_orm.models.Person
    person_seeder(Person, 10, { 'string': None })
    target_node_alias = person_datatype_node_alias_keys['string'][-1];

    def _equal(value: str = 'parker'):
        person_seeder(Person, 3, { 'string': value })
        records = Person.where(**{f"{target_node_alias}": value}).get()

        for record in records:
            assert(get_nested_datatype_value(record, 'string') == value)

    def _not_equals(value: str = 'parker'):
        person_seeder(Person, 3, { 'string': value })
        operator = random.choice(NOT_EQUAL_KEYS)
        records = Person.where(**{f"{target_node_alias}__{operator}": value}).get()

        for record in records:
            assert(get_nested_datatype_value(record, 'string') != value)

    def _contains(value: str = 'parker'):
        sub_string = value[:(len(value) // 2)]
        person_seeder(Person, 3, { 'string': value })
        operator = random.choice(CONTAINS_KEYS)
        records = Person.where(**{f"{target_node_alias}__{operator}": sub_string}).get()

        for record in records:
            assert(sub_string in get_nested_datatype_value(record, 'string'))

    def _insensitive_contains(value: str = 'parker'):
        sub_string = (value[:(len(value) // 2)]).upper()
        person_seeder(Person, 3, { 'string': value })
        operator = random.choice(INSENSITIVE_CONTAINS_KEYS)
        records = Person.where(**{f"{target_node_alias}__{operator}": sub_string}).get()

        for record in records:
            assert(sub_string.lower() in get_nested_datatype_value(record, 'string').lower())

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

def sub_test_filter_where_number_quries(arches_orm):
    Person = arches_orm.models.Person
    person_seeder(Person, 10, { 'number': None })
    target_node_alias = person_datatype_node_alias_keys['number'][-1];

    def _greater_than(value: int = 50):
        operator = random.choice(GREATER_THAN_KEYS)
        records = Person.where(**{f"{target_node_alias}__{operator}": value}).get()
        for record in records:
            assert(get_nested_datatype_value(record, 'number') > value)

    def _less_than(value: int = 50):
        operator = random.choice(LESS_THAN_KEYS)
        records = Person.where(**{f"{target_node_alias}__{operator}": value}).get()
        for record in records:
            assert(get_nested_datatype_value(record, 'number') < value)

    def _less_than_or_equal(value: int = 50):
        operator = random.choice(LESS_THAN_OR_EQUAL_KEYS)
        records = Person.where(**{f"{target_node_alias}__{operator}": value}).get()
        for record in records:
            assert(get_nested_datatype_value(record, 'number') <= value)

    def _greater_than_or_equal(value: int = 50):
        operator = random.choice(GREATER_THAN_OR_EQUAL_KEYS)
        records = Person.where(**{f"{target_node_alias}__{operator}": value}).get()
        for record in records:
            assert(get_nested_datatype_value(record, 'number') >= value)

    def _equal(value: int = 23):
        person_seeder(Person, 3, { 'number': value })
        records = Person.where(**{f"{target_node_alias}": value}).get()
        for record in records:
            assert(get_nested_datatype_value(record, 'number') == value)

    def _not_equals(value: int = 23):
        person_seeder(Person, 3, { 'number': value })
        operator = random.choice(NOT_EQUAL_KEYS)
        records = Person.where(**{f"{target_node_alias}__{operator}": value}).get()

        for record in records:
            assert(get_nested_datatype_value(record, 'number') != value)

    _greater_than(30)
    _greater_than(70)
    _greater_than(20)

    _less_than(10)
    _less_than(53)
    _less_than(23)

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

# def sub_test_filter_where_number_equal(arches_orm):
#     Person = arches_orm.models.Person
    
#     person_seeder(Person, 10, {'number': number_seeder_odd_even })
        
#     records = Person.where(primary_reference_number=1).get();
#     assert(len(records) == 5)

#     for record in records:
#         assert(record.system_reference_numbers.primaryreferencenumber.primary_reference_number == 1)

# def sub_test_filter_where_date_datatype(arches_orm):
#     Person = arches_orm.models.Person
#     person_seeder(Person, 10, { 'date': date_seeder_50_50_precent_older_future_dates_from_present })

#     today_date = now().date()

#     print('TODAYS DATE : ', today_date)

#     records = Person.where(creation_end_date__lt=today_date).get();
#     for record in records:
#         print('FROM LOOP: ', record.audit_metadata.audit_creation.creation_timespan.creation_end_date)

#     assert(len(records) == 5)

#     records = Person.where(creation_end_date__gt=today_date).get();
#     assert(len(records) == 5)