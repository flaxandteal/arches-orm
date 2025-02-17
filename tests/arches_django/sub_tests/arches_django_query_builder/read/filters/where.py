from tests.utilities.common import create_tile_from_model
from tests.utilities.seeders.default.person import person_primary_reference_number_odd_even_seeder, person_primary_date_50_50_older_past_seeder
from datetime import datetime

def sub_test_filter_where(arches_orm):
    sub_test_filter_where_number_equal(arches_orm)
    sub_test_filter_where_date_equal(arches_orm)

def sub_test_filter_where_number_equal(arches_orm):
    Person = arches_orm.models.Person
    person_primary_reference_number_odd_even_seeder(Person, 10)
        
    records = Person.where(primary_reference_number=1).get();
    assert(len(records) == 5)

    for record in records:
        assert(record.system_reference_numbers.primaryreferencenumber.primary_reference_number == 1)

def sub_test_filter_where_date_equal(arches_orm):
    Person = arches_orm.models.Person
    person_primary_date_50_50_older_past_seeder(Person, 10)

    today_date = datetime.today().strftime("%Y-%m-%d")

    records = Person.where(associated_actor_start_date__lt=today_date).get();
    print(len(records))
    assert(len(records) == 5)
