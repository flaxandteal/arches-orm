from tests.utilities.common import create_tile_from_model

def person_basic_seeder(model, amount: int):
    includes = [
        'name', 
            'full_name', 
        'system_reference_numbers', 
            'primaryreferencenumber',
                'primary_reference_number'
    ]

    # def custom_value_full_name():
    #     import random
    #     return random.choice(['UP', 'DOWN'])

    for _ in range(amount):
        person = create_tile_from_model(
            model.create(), 
            includes=includes
        )
        person.save() 

def person_primary_reference_number_odd_even_seeder(model, amount: int):
    includes = [
        'system_reference_numbers', 
            'primaryreferencenumber',
                'primary_reference_number'
    ]

    for index in range(amount):
        def custom_value_primary_refernce_number():
            nonlocal index

            if (index % 2 == 0):
                return 2
            
            return 1

        person = create_tile_from_model(
            model.create(), 
            includes=includes,
            custom_seed_values={ 'primary_reference_number': custom_value_primary_refernce_number }
        )
        person.save() 