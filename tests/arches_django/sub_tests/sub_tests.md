# Purpose
This documentation is about the sub_tests folder and the reason for this folder structure is to allow sub tests, therefore we can use these sub tests with different Django fixtures. These Django fixtures have different user roles and permissions for example @ContextFree is like a super admin.

# Structure Layout
The folder structure is below, you can customise the children structure (folders/file) as you please, however we do name the parent folder the same file as
the parent test folder
```
.
└── sub_tests/
    └── f'{parent_test_folder_name}'/
        └── folders/file
```

# Sub test file structure towards methods
You can see below an example of how I have achieved the structure of the sub tests. Every sub test file should contain atleast 1 method which calls all the 
sub tests, in the example below this would be "sub_test_selector_find" as this calls all the sub tests ("sub_test_selector_find_includes" & "sub_test_selector_find_expect").

Also I want to point out that the methods naming convention have a hierarchy system, therefore if defined in the parent testing file, its easy to idenifity where the test belongs towards.


```python
def sub_test_selector_find(arches_orm):
    sub_test_selector_find_expect(arches_orm)
    sub_test_selector_find_includes(arches_orm)

def sub_test_selector_find_expect(arches_orm):
    def _test_find():
        Person = arches_orm.models.Person
        person = Person.create()
        ash = person.name.append()
        random_uuid = str(uuid.uuid4())
        ash.full_name = random_uuid
        person.save()
        resource_instance_id = person._.id


        found = Person.find(resource_instance_id=resource_instance_id)
        assert(found[0].name[0].full_name == random_uuid)
        assert(len(found) == 1)
        
    _test_find()
    _test_find()
    _test_find()
    _test_find()

def sub_test_selector_find_includes(arches_orm):
    ...
```