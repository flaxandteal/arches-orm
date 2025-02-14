from tests.utilities.common import create_tile_from_model

def sub_test_or_where_equal(arches_orm):
    Person = arches_orm.models.Person

    def seed():
        includes = [
            'system_reference_numbers', 
                'primaryreferencenumber',
                    'primary_reference_number'
        ]

        amount = 50

        for index in range(amount):
            def custom_value_primary_refernce_number():
                nonlocal index

                if index % 3 == 0:
                    return 42
                elif index % 3 == 1:
                    return 87
                else:
                    return 99

            person = create_tile_from_model(
                Person.create(), 
                includes=includes,
                custom_seed_values={'primary_reference_number': custom_value_primary_refernce_number}
            )
            person.save() 
        
    seed()

    records = Person.where(primary_reference_number=42).or_where(primary_reference_number=87).get();

    assert(len(records) == 34)

    valid_values = [42, 87]

    for record in records:
        assert(record.system_reference_numbers.primaryreferencenumber.primary_reference_number in valid_values)