from tests.utilities.common import create_tile_from_model

def all_check_default(arches_orm):
    """
    This method checks if the length amount matches the entire all from records

    Args:
        arches_orm (any): The arches orm gained from the apdaptor
    """

    Person = arches_orm.models.Person
    includes = [
        'name', 
            'full_name', 
        'system_reference_numbers', 
            'primaryreferencenumber',
                'primary_reference_number'
    ]

    def custom_value_full_name():
        import random
        return random.choice(['UP', 'DOWN'])

    amount = 50

    for _ in range(amount):
        person = create_tile_from_model(
            Person.create(), 
            includes=includes,
            custom_seed_values={ 'full_name': custom_value_full_name }
        )
        person.save() 
        
    records = Person.all(page=None);

    # print('THIS IS THE VALUE HERE! : ', records[0].system_reference_numbers.primaryreferencenumber.primary_reference_number)
    # print('THIS IS THE VALUE HERE! : ', records[0].name[0].full_name)

    assert(len(records) == amount)