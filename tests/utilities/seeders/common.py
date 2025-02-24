def number_seeder_odd_even(index: None | int):
        if (index % 2 == 0):
            return 2
        
        return 1

def number_seeder_use_index_as_value(index):
    return index

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