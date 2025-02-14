from tests.utilities.common import create_tile_from_model
from tests.utilities.seeders.default.person import person_basic_seeder

def sub_test_selector_all(arches_orm):
    sub_test_selector_all_amount(arches_orm)

def sub_test_selector_all_amount(arches_orm):
    """
    This method checks if the length amount matches the entire all from records

    Args:
        arches_orm (any): The arches orm gained from the apdaptor
    """
    Person = arches_orm.models.Person

    person_basic_seeder(Person, 10)
    records = Person.all();
    assert(len(records) == 10)

    person_basic_seeder(Person, 16)
    records = Person.all();
    assert(len(records) == 26)

    person_basic_seeder(Person, 20)
    records = Person.all();
    assert(len(records) == 46)
