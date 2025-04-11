from tests.utilities.seeders.seeder import Seeder
from tests.utilities.seeders.default.config import PERSON_DATATYPE_NODE_ALIAS_KEYS, PERSON_DEFAULT_SEED_PATH

def sub_test_selector_first(arches_orm):
    instance_arches_orm_model_person = arches_orm.models.Person
    instance_person_seeder = Seeder(instance_arches_orm_model_person, PERSON_DATATYPE_NODE_ALIAS_KEYS, PERSON_DEFAULT_SEED_PATH)

    sub_test_selector_first_amount(instance_arches_orm_model_person, instance_person_seeder)

def sub_test_selector_first_amount(instance_arches_orm_model_person, instance_person_seeder):
    target_node_alias = PERSON_DATATYPE_NODE_ALIAS_KEYS['string'][-1];

    instance_person_seeder.seed(2, { 'string': None })
    instance_person_seeder.seed(1, { 'string': 'RABBIT' })
    instance_person_seeder.seed(2, { 'string': 'MOLE' })

    record = instance_arches_orm_model_person.where(**{f"{target_node_alias}": 'RABBIT' }).or_where(**{f"{target_node_alias}": 'MOLE' }).order_by(target_node_alias).first()    
    assert(instance_person_seeder.get_nested_datatype_value(record, 'string') == 'MOLE')