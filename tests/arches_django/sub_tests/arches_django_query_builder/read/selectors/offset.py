from tests.utilities.seeders.seeder import Seeder
from tests.utilities.seeders.default.consts import PERSON_DATATYPE_NODE_ALIAS_KEYS

def sub_test_selector_offset(arches_orm):
    instance_arches_orm_model_person = arches_orm.models.Person
    instance_person_seeder = Seeder(instance_arches_orm_model_person, PERSON_DATATYPE_NODE_ALIAS_KEYS)

    sub_test_selector_offset_amount(instance_arches_orm_model_person, instance_person_seeder)


def sub_test_selector_offset_amount(instance_arches_orm_model_person, instance_person_seeder):
    """
    This method checks if the length amount matches the entire all from records

    Args:
        arches_orm (any): The arches orm gained from the apdaptor
    """

    def _custom_number_handle(index: int):
        return index + 1;

    instance_person_seeder.seed(30, seed_datatypes={ 'number': _custom_number_handle })

    def _assert_limit_offset_query_results(offset: int, limit: int):
        records = instance_arches_orm_model_person.offset(offset, limit);
        assert(len(records) == limit)
        for index, record in enumerate(records):
            assert(instance_person_seeder.get_nested_datatype_value(record, 'number') == offset + _custom_number_handle(index))

    _assert_limit_offset_query_results(5, 7)
    _assert_limit_offset_query_results(10, 5)
    _assert_limit_offset_query_results(10, 8)

    def _assert_limit_query_results(limit: int):
        records = instance_arches_orm_model_person.offset(limit=limit);
        assert(len(records) == limit)

    _assert_limit_query_results(5)
    _assert_limit_query_results(10)
    _assert_limit_query_results(15)

    def _assert_offset_query_results(offset: int):
        records = instance_arches_orm_model_person.offset(offset=offset);
        for index, record in enumerate(records):
            assert(instance_person_seeder.get_nested_datatype_value(record, 'number') == offset + _custom_number_handle(index))

    _assert_offset_query_results(5)
    _assert_offset_query_results(10)
    _assert_offset_query_results(15)



