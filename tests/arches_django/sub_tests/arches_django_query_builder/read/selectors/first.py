from tests.utilities.seeders.default.person import person_seeder
from tests.utilities.seeders.default.person import person_seeder, get_nested_datatype_value

def sub_test_selector_first(arches_orm):
    sub_test_selector_first_amount(arches_orm)

def sub_test_selector_first_amount(arches_orm):
    Person = arches_orm.models.Person

    def _custom_number_handle(index: int):
        return index + 1;

    person_seeder(Person, 5, seed_datatypes={ 'number': _custom_number_handle })

    records = Person.first();

    assert(len(records) == 1)
    assert(get_nested_datatype_value(records[0], 'number') == 1)