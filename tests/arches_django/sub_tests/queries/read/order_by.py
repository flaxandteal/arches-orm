from tests.utilities.common import create_tile_from_model

def sub_test_order_by_ascend(arches_orm):
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
            return index

        person = create_tile_from_model(
            Person.create(), 
            includes=includes,
            custom_seed_values={ 'primary_reference_number': custom_value_primary_refernce_number }
        )
        person.save() 
        
    records = Person.order_by('-primary_reference_number').get();

    # assert(len(records) == 25)

    for record in records:
        print(record.system_reference_numbers.primaryreferencenumber.primary_reference_number)
        # assert(record.system_reference_numbers.primaryreferencenumber.primary_reference_number == 87)