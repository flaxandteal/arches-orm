from tests.utilities.seeders.seeder import Seeder
from tests.utilities.seeders.default.consts import PERSON_DATATYPE_NODE_ALIAS_KEYS

def sub_test_selector_first(arches_orm):
    instance_arches_orm_model_person = arches_orm.models.Person
    instance_person_seeder = Seeder(instance_arches_orm_model_person, PERSON_DATATYPE_NODE_ALIAS_KEYS)

    sub_test_selector_first_amount(instance_arches_orm_model_person, instance_person_seeder)

def sub_test_selector_first_amount(instance_arches_orm_model_person, instance_person_seeder):
    target_node_alias = PERSON_DATATYPE_NODE_ALIAS_KEYS['string'][-1];

    instance_person_seeder.seed(2, { 'string': None })
    instance_person_seeder.seed(1, { 'string': 'RABBIT' })
    instance_person_seeder.seed(2, { 'string': 'MOLE' })

    records = instance_arches_orm_model_person.where(**{f"{target_node_alias}": 'RABBIT' }).or_where(**{f"{target_node_alias}": 'MOLE' }).first()

    assert(len(records) == 1)
    assert(instance_person_seeder.get_nested_datatype_value(records[0], 'string') == 'RABBIT')