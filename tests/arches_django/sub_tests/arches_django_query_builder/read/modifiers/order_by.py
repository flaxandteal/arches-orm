from tests.utilities.common import create_tile_from_model
from tests.utilities.seeders.common import number_seeder_odd_even, number_seeder_use_index_as_value, date_seeder_50_50_precent_older_future_dates_from_present
from tests.utilities.seeders.default.person import person_seeder, get_nested_datatype_value, person_datatype_node_alias_keys
from datetime import datetime
from django.db.models import Func, F, ExpressionWrapper, FloatField, CharField, DateTimeField, OuterRef, Subquery, BooleanField

from arches.app.models.models import TileModel
from tests.utilities.seeders.seeder import Seeder
from tests.utilities.seeders.default.consts import PERSON_DATATYPE_NODE_ALIAS_KEYS

def sub_test_modifier_order_by(arches_orm):
    instance_arches_orm_model_person = arches_orm.models.Person
    instance_person_seeder = Seeder(instance_arches_orm_model_person, PERSON_DATATYPE_NODE_ALIAS_KEYS)

    sub_test_modifier_order_by_date_order(instance_arches_orm_model_person, instance_person_seeder)
    sub_test_modifier_order_by_number_order(instance_arches_orm_model_person, instance_person_seeder)

def expression_number_datatype(nodeid: str) -> ExpressionWrapper:
    """
    Method gets the experssion for a number datatype. This is mainaly used for the tiles JSON column that is stored within the database so we can use
    annotations around the expressions

    Args:
        nodeid (str): The node id

    Returns:
        ExpressionWrapper: This is the expression wrapper that is returned and should be mainly used for annotations
    """
    return ExpressionWrapper(
        F(f'data__{nodeid}'),
        output_field=FloatField()
    )

def sub_test_modifier_order_by_number_order(instance_arches_orm_model_person, instance_person_seeder):
    target_node_alias = PERSON_DATATYPE_NODE_ALIAS_KEYS['number'][-1];

    def _sub_test():
        instance_person_seeder.seed(4, { 'number': number_seeder_odd_even, 'string': None })
        descending_records = instance_arches_orm_model_person.order_by(f'-{target_node_alias}').get()
        ascending_records = instance_arches_orm_model_person.order_by(target_node_alias).get()

        previous_number_value = None

        for acend_record in ascending_records:
            record_number_value = get_nested_datatype_value(acend_record, 'number')
            if (record_number_value is None): continue;

            if previous_number_value is None:
                previous_number_value = record_number_value
                continue;
            
            assert(record_number_value >= previous_number_value)
            previous_number_value = record_number_value

        previous_number_value = None

        for descend_record in descending_records:
            record_number_value = get_nested_datatype_value(descend_record, 'number')
            if (record_number_value is None): continue;

            if previous_number_value is None:
                previous_number_value = record_number_value
                continue;
            
            assert(record_number_value <= previous_number_value)
            previous_number_value = record_number_value

    _sub_test()
    _sub_test()
    _sub_test()

def sub_test_modifier_order_by_date_order(instance_arches_orm_model_person, instance_person_seeder):
    target_node_alias = PERSON_DATATYPE_NODE_ALIAS_KEYS['date'][-1];

    def _sub_test():
        instance_person_seeder.seed(5, { 'date': date_seeder_50_50_precent_older_future_dates_from_present })
        descending_records = instance_arches_orm_model_person.order_by(f'-{target_node_alias}').get()
        ascending_records = instance_arches_orm_model_person.order_by(f'{target_node_alias}').get()

        previous_date = None;

        for ascend_record in ascending_records: 
            record_date = str(get_nested_datatype_value(ascend_record, 'date'))
            if (record_date is None): continue;

            if not previous_date:
                previous_date = datetime.fromisoformat(record_date);
                continue;
            
            current_date = datetime.fromisoformat(record_date);

            assert(current_date >= previous_date)
            previous_date = current_date
            
        previous_date = None;
        
        for descend_record in descending_records:
            record_date = str(get_nested_datatype_value(descend_record, 'date'))
            if (record_date is None): continue;

            if not previous_date:
                previous_date = datetime.fromisoformat(record_date);
                continue;
            
            current_date = datetime.fromisoformat(record_date);
            assert(current_date <= previous_date)
            previous_date = current_date

    _sub_test()
    _sub_test()
    _sub_test()

