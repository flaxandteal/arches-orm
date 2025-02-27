from tests.utilities.seeders.default.person import person_seeder
from tests.utilities.seeders.default.person import person_seeder, get_nested_datatype_value
from tests.utilities.common import print_table_data
import uuid

def sub_test_selector_find(arches_orm):
    sub_test_selector_find_expect(arches_orm)

def sub_test_selector_find_expect(arches_orm):
    def _test_find():
        Person = arches_orm.models.Person
        person = Person.create()
        ash = person.name.append()
        random_uuid = str(uuid.uuid4())
        ash.full_name = random_uuid
        person.save()
        resource_instance_id = person._.id
        found = Person.find(str(resource_instance_id))
    
        print('SEARCH FOR RESOURCE INSTANCE : ', resource_instance_id)
        print('RESOURCE INSTANCE ID FROM FOUND : ', found[0]._.id)
        print('THIS IF THE FOUND UUID : ', found[0].name[0].full_name)
        print('THIS IF THE RANDOM UUID : ', random_uuid)
        print_table_data('tiles')
        print('----------------------------------')
        assert(found[0].name[0].full_name == random_uuid)
        assert(len(found) == 1)

    _test_find()
    _test_find()
    _test_find()
    _test_find()