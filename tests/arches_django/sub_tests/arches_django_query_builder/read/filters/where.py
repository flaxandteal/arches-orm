from tests.utilities.common import create_tile_from_model
from tests.utilities.seeders.default.person import person_primary_reference_number_odd_even_seeder, person_date_field_seeder
from datetime import datetime
import random
from datetime import datetime, timedelta
from django.utils.timezone import now

def _custom_callback_date_50_50_older_present_seed(index: int):
    index = random.randint(0, 100)
    today = datetime.today()
    days_ahead = random.randint(1, 5 * 365)

    if index % 2 == 0:
        future_date = today + timedelta(days=days_ahead)
    else:
        future_date = today - timedelta(days=days_ahead)

    return future_date.strftime("%Y-%m-%d")

def sub_test_filter_where(arches_orm):
    sub_test_filter_where_number_equal(arches_orm)
    sub_test_filter_where_date_datatype(arches_orm)

def sub_test_filter_where_number_equal(arches_orm):
    Person = arches_orm.models.Person
    person_primary_reference_number_odd_even_seeder(Person, 10)
        
    records = Person.where(primary_reference_number=1).get();
    assert(len(records) == 5)

    for record in records:
        assert(record.system_reference_numbers.primaryreferencenumber.primary_reference_number == 1)

def sub_test_filter_where_date_datatype(arches_orm):
    Person = arches_orm.models.Person
    person_date_field_seeder(Person, 10, _custom_callback_date_50_50_older_present_seed)

    today_date = now().date()

    print('TODAYS DATE : ', today_date)

    records = Person.where(creation_end_date__lt=today_date).get();
    for record in records:
        print('FROM LOOP: ', record.audit_metadata.audit_creation.creation_timespan.creation_end_date)

    assert(len(records) == 5)

    records = Person.where(creation_end_date__gt=today_date).get();
    assert(len(records) == 5)