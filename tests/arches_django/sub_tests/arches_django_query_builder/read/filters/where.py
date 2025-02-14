from tests.utilities.common import create_tile_from_model
from tests.utilities.seeders.default.person import person_primary_reference_number_odd_even_seeder

def sub_test_filter_where(arches_orm):
    sub_test_filter_where_number_equal(arches_orm)

def sub_test_filter_where_number_equal(arches_orm):
    Person = arches_orm.models.Person
    person_primary_reference_number_odd_even_seeder(Person, 10)
        
    records = Person.where(primary_reference_number=1).get();
    assert(len(records) == 5)

    for record in records:
        assert(record.system_reference_numbers.primaryreferencenumber.primary_reference_number == 1)