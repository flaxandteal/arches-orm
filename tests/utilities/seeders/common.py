def number_seeder_odd_even(index: None | int):
        if (index % 2 == 0):
            return 2
        
        return 1

def number_seeder_use_index_as_value(index):
    return index

def boolean_seeder_50_50_false_true(index):
    if (index % 2 == 0): return True
    return False

def date_seeder_50_50_precent_older_future_dates_from_present(index: int):
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

def date_seeder_33_precent_present_past_future_dates_from_present(index: int) -> str:
    """
    Method handles getting the date as seed data for the datatype date, however in this case, we have 3 options to choice from
    which is todays date, past date or future date

    Args:
        index (int): Loop index towards the seeder

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