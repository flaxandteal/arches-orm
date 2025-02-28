import uuid
import random
from tests.utilities.seeders.seeder import Seeder
from tests.utilities.seeders.default.config import PERSON_DATATYPE_NODE_ALIAS_KEYS, PERSON_DEFAULT_SEED_PATH

def sub_test_selector_find(arches_orm):
    instance_arches_orm_model_person = arches_orm.models.Person
    instance_person_seeder = Seeder(instance_arches_orm_model_person, PERSON_DATATYPE_NODE_ALIAS_KEYS, PERSON_DEFAULT_SEED_PATH)

    sub_test_selector_find_expect(instance_arches_orm_model_person, instance_person_seeder)

def sub_test_selector_find_expect(instance_arches_orm_model_person, instance_person_seeder):
    def _test_find():
        amount = random.randrange(3, 5)
        find_index = random.randrange(0, amount - 1)

        assert_string = None;
        find_resource_id = None;

        for index in range(amount):
            random_uuid = str(uuid.uuid4())
            person = instance_person_seeder.seed(1, { 'string': random_uuid })[0]

            if (find_index == index):
                find_resource_id = person._.id
                assert_string = random_uuid;

           
        found_record = instance_arches_orm_model_person.find(str(find_resource_id))
        assert(instance_person_seeder.get_nested_datatype_value(found_record, 'string') == assert_string)

    _test_find()
    _test_find()