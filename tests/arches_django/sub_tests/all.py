from tests.utilities.common import create_tile_from_model

def all_check_default(arches_orm):
    """
    This method checks if the length amount matches the entire all from records

    Args:
        arches_orm (any): The arches orm gained from the apdaptor
    """

    Person = arches_orm.models.Person
    includes = ['name', 'full_name']
    amount = 50

    for _ in range(amount):
        person = create_tile_from_model(Person.create(), includes=includes)
        person.save() 

    records = Person.all(page=None);

    assert(len(records) == amount)