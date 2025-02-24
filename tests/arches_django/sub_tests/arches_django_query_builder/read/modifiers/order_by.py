from tests.utilities.common import create_tile_from_model
from tests.utilities.seeders.common import number_seeder_odd_even, number_seeder_use_index_as_value, date_seeder_50_50_precent_older_future_dates_from_present
from tests.utilities.seeders.default.person import person_seeder, get_nested_datatype_value, person_datatype_node_alias_keys
from datetime import datetime

def sub_test_modifier_order_by(arches_orm):
    # sub_test_modifier_order_by_date_order(arches_orm)
    sub_test_modifier_order_by_number_order(arches_orm)

def sub_test_modifier_order_by_number_order(arches_orm):
    Person = arches_orm.models.Person
    target_node_alias = person_datatype_node_alias_keys['number'][-1];

    def _sub_test():
        person_seeder(Person, 5, { 'number': True })
        descending_records = Person.order_by(f'-{target_node_alias}').get()
        ascending_records = Person.order_by(f'{target_node_alias}').get()

        previous_number_value = None

        for acend_record in ascending_records:
            record_number_value = get_nested_datatype_value(acend_record, 'number')

            if previous_number_value == None:
                previous_number_value = record_number_value
                continue;
            
            assert(record_number_value >= previous_number_value)
            previous_number_value = record_number_value

        previous_number_value = None

        for descend_record in descending_records:
            record_number_value = get_nested_datatype_value(descend_record, 'number')

            if previous_number_value == None:
                previous_number_value = record_number_value
                continue;
            
            assert(record_number_value <= previous_number_value)
            previous_number_value = record_number_value

    _sub_test()
    _sub_test()
    _sub_test()

def sub_test_modifier_order_by_date_order(arches_orm):
    Person = arches_orm.models.Person
    target_node_alias = person_datatype_node_alias_keys['date'][-1];

    def _sub_test():
        person_seeder(Person, 5, { 'date': date_seeder_50_50_precent_older_future_dates_from_present })
        descending_records = Person.order_by(f'-{target_node_alias}').get()
        ascending_records = Person.order_by(f'{target_node_alias}').get()

        previous_date = None;

        for ascend_record in ascending_records: 
            record_date = str(get_nested_datatype_value(ascend_record, 'date'))

            if not previous_date:
                previous_date = datetime.fromisoformat(record_date);
                continue;
            
            current_date = datetime.fromisoformat(record_date);
            assert(current_date >= previous_date)
            previous_date = current_date
            
        previous_date = None;
        
        for descend_record in descending_records:
            record_date = str(get_nested_datatype_value(descend_record, 'date'))

            if not previous_date:
                previous_date = datetime.fromisoformat(record_date);
                continue;
            
            current_date = datetime.fromisoformat(record_date);
            assert(current_date <= previous_date)
            previous_date = current_date

    _sub_test()
    _sub_test()
    _sub_test()

