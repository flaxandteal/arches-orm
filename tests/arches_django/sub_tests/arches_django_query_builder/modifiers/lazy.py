from tests.utilities.seeders.seeder import Seeder
from tests.utilities.seeders.default.config import PERSON_DATATYPE_NODE_ALIAS_KEYS, PERSON_DEFAULT_SEED_PATH

def sub_test_modifier_lazy(arches_orm):
    instance_arches_orm_model_person = arches_orm.models.Person
    instance_person_seeder = Seeder(instance_arches_orm_model_person, PERSON_DATATYPE_NODE_ALIAS_KEYS, PERSON_DEFAULT_SEED_PATH)

    sub_test_modifier_lazy_loaded_check(instance_arches_orm_model_person, instance_person_seeder)

def sub_test_modifier_lazy_loaded_check(instance_arches_orm_model_person, instance_person_seeder):
    import random

    target_node_alias = PERSON_DATATYPE_NODE_ALIAS_KEYS['string'][-1];
    
    def _sub_test():
        random_number = random.randint(1, 10)
        instance_person_seeder.seed(random_number, { 'string': 'TEST' })

        # * Since its lazy loading tiles, there should be no data within ValueList's _values on the wrapper as it loads once the attribute is called
        lazy_records = instance_arches_orm_model_person.where(**{target_node_alias: 'TEST'}).lazy().get();
        for lazy_record in lazy_records:
            assert(len(lazy_record._._values) == 0)

        # * Since its non lazy loading tiles, there should be data within ValueList's _values on the wrapper
        non_lazy_records = instance_arches_orm_model_person.where(**{target_node_alias: 'TEST'}).get();
        for non_lazy_record in non_lazy_records:
            assert(len(non_lazy_record._._values) > 0)

    _sub_test()
    _sub_test()
    _sub_test()
