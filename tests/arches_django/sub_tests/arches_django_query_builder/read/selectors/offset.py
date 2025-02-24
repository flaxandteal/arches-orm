from tests.utilities.seeders.default.person import person_seeder
from tests.utilities.seeders.default.person import person_seeder, get_nested_datatype_value

def sub_test_selector_offset(arches_orm):
    sub_test_selector_offset_amount(arches_orm)

def sub_test_selector_offset_amount(arches_orm):
    """
    This method checks if the length amount matches the entire all from records

    Args:
        arches_orm (any): The arches orm gained from the apdaptor
    """
    Person = arches_orm.models.Person

    def _custom_number_handle(index: int):
        return index;

    person_seeder(Person, 30, seed_datatypes={ 'number': _custom_number_handle })

    def _assert_limit_offset_query_results(offset: int, limit: int):
        records = Person.offset(offset, limit);
        assert(len(records) == limit)
        for index, record in enumerate(records):
            assert(get_nested_datatype_value(record, 'number') == offset + index)

    _assert_limit_offset_query_results(5, 7)
    _assert_limit_offset_query_results(10, 5)
    _assert_limit_offset_query_results(10, 8)

    def _assert_limit_query_results(limit: int):
        records = Person.offset(limit=limit);
        assert(len(records) == limit)

    _assert_limit_query_results(5)
    _assert_limit_query_results(10)
    _assert_limit_query_results(15)

    def _assert_offset_query_results(offset: int):
        records = Person.offset(offset=offset);
        for index, record in enumerate(records):
            assert(get_nested_datatype_value(record, 'number') == offset + index)

    _assert_offset_query_results(5)
    _assert_offset_query_results(10)
    _assert_offset_query_results(15)



