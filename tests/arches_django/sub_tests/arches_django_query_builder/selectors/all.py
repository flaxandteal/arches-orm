from tests.utilities.seeders.seeder import Seeder
from tests.utilities.seeders.default.config import PERSON_DATATYPE_NODE_ALIAS_KEYS, PERSON_DEFAULT_SEED_PATH

def sub_test_selector_all(arches_orm):
    instance_arches_orm_model_person = arches_orm.models.Person
    instance_person_seeder = Seeder(instance_arches_orm_model_person, PERSON_DATATYPE_NODE_ALIAS_KEYS, PERSON_DEFAULT_SEED_PATH)

    sub_test_selector_all_amount(instance_arches_orm_model_person, instance_person_seeder)

def sub_test_selector_all_amount(instance_arches_orm_model_person, instance_person_seeder):
    import random

    previous_count = 0

    def _sub_test():
        nonlocal previous_count
        
        random_number = random.randint(1, 10)

        instance_person_seeder.seed(random_number, { 'string': None })
        records = instance_arches_orm_model_person.all();

        previous_count = previous_count + random_number

        assert(len(records) == previous_count)

    _sub_test()
    _sub_test()
    _sub_test()
