from tests.utilities.common import create_tile_from_model

def sub_test_where_equal(arches_orm):
    Person = arches_orm.models.Person
    includes = [
        'system_reference_numbers', 
            'primaryreferencenumber',
                'primary_reference_number'
    ]

    amount = 50

    for index in range(amount):
        def custom_value_primary_refernce_number():
            nonlocal index

            if (index % 2 == 0):
                return 42
            
            return 87

        person = create_tile_from_model(
            Person.create(), 
            includes=includes,
            custom_seed_values={ 'primary_reference_number': custom_value_primary_refernce_number }
        )
        person.save() 
        
    records = Person.where(primary_reference_number=87).get();
    assert(len(records) == 25)

    for record in records:
        assert(record.system_reference_numbers.primaryreferencenumber.primary_reference_number == 87)