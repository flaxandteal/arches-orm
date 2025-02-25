from tests.utilities.seeders.default.person import person_seeder
from tests.utilities.seeders.default.person import person_seeder, get_nested_datatype_value
import uuid

def sub_test_selector_find(arches_orm):
    sub_test_selector_find_expect(arches_orm)

def sub_test_selector_find_expect(arches_orm):
    # def _test_find():
    #     Person = arches_orm.models.Person
    #     person = Person.create()
    #     ash = person.name.append()
    #     random_uuid = str(uuid.uuid4())
    #     ash.full_name = random_uuid
    #     person.save()
    #     resource_instance_id = person._.id


    #     found = Person.find(resource_instance_id=resource_instance_id)
    #     assert(found[0].name[0].full_name == random_uuid)
    #     assert(len(found) == 1)
        
    def _test_find():
        Person = arches_orm.models.Person
        person = Person.create()
        ash = person.name.append()
        random_uuid = str(uuid.uuid4())
        ash.full_name = random_uuid
        person.save()
        resource_instance_id = person._.id


        found = Person.lazy().find(resource_instance_id)
        # assert(found[0].name[0].full_name == random_uuid)
        # assert(len(found) == 1)
        print('FOUND DATA : ', found[0].name[0].full_name)

    _test_find()
    _test_find()
    _test_find()
    _test_find()