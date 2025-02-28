def number_seeder_odd_even(index: None | int) -> int:
    """
    Method just returns a odd or even, depending on the index

    Args:
        index (None | int): This is the loop index, should come from the seeder

    Returns:
        int: An odd or even int value
    """
    if (index % 2 == 0):
        return 2
    
    return 1

def number_seeder_use_index_as_value(index: None | int) -> int:
    """
    Method just returns the loop index

    Args:
        index (None | int): This is the loop index, should come from the seeder

    Returns:
        int: Returns the loop index
    """
    return index

def boolean_seeder_50_50_false_true(index: None | int) -> bool:
    """
    Method has a 50/50 chance of returning True or False, depending on the index

    Args:
        index (None | int): This is the loop index, should come from the seeder

    Returns:
        bool: This is the 50/50 value returned
    """
    if (index % 2 == 0): return True
    return False

def date_seeder_50_50_precent_older_future_dates_from_present(index: int | None) -> str:
    """
    Method has a 50/50 chance of returning a future or past date from the present date

    Args:
        index (None | int): This is the loop index, should come from the seeder

    Returns:
        str: Future or past date
    """
    import random
    from datetime import datetime, timedelta

    index = random.randint(0, 100)
    today = datetime.today()
    days_ahead = random.randint(1, 5 * 365)

    if index % 2 == 0:
        future_date = today + timedelta(days=days_ahead)
    else:
        future_date = today - timedelta(days=days_ahead)

    return future_date.strftime("%Y-%m-%d")

def date_seeder_33_precent_present_past_future_dates_from_present(index: int | None) -> str:
    """
    Method handles getting the date as seed data for the datatype date, however in this case, we have 3 options to choice from
    which is todays date, past date or future date

    Args:
        index (None | int): This is the loop index, should come from the seeder

    Returns:
        str: Returns a future or today or past date
    """
    import random
    from datetime import datetime, timedelta

    index = random.randint(0, 100)
    today = datetime.today()
    days_ahead = random.randint(1, 5 * 365)

    if index % 3 == 0:
        future_date = today
    elif index % 2 == 0:
        future_date = today + timedelta(days=days_ahead)
    else:
        future_date = today - timedelta(days=days_ahead)

    return future_date.strftime("%Y-%m-%d")