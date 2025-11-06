"""
Brazilian Banking Calendar
Handles business days and national holidays for banking operations.
"""
from datetime import date, timedelta
from dateutil.easter import easter


def get_brazilian_holidays(year):
    """
    Get list of Brazilian national banking holidays for a given year.
    """
    holidays = [
        date(year, 1, 1),
        date(year, 4, 21),
        date(year, 5, 1),
        date(year, 9, 7),
        date(year, 10, 12),
        date(year, 11, 2),
        date(year, 11, 15),
        date(year, 12, 25),
    ]
    
    easter_date = easter(year)
    holidays.extend([
        easter_date - timedelta(days=47),
        easter_date - timedelta(days=46),
        easter_date - timedelta(days=2),
        easter_date,
        easter_date + timedelta(days=60),
    ])
    
    return sorted(holidays)


def is_business_day(check_date):
    """
    Check if a date is a business day in Brazil.
    Business days exclude weekends and national holidays.
    """
    if check_date.weekday() >= 5:
        return False
    
    holidays = get_brazilian_holidays(check_date.year)
    if check_date in holidays:
        return False
    
    return True


def get_business_days_between(start_date, end_date):
    """
    Count business days between two dates (inclusive).
    """
    if start_date > end_date:
        start_date, end_date = end_date, start_date
    
    business_days = 0
    current_date = start_date
    
    while current_date <= end_date:
        if is_business_day(current_date):
            business_days += 1
        current_date += timedelta(days=1)
    
    return business_days


def get_next_business_day(check_date):
    """
    Get the next business day after the given date.
    """
    next_day = check_date + timedelta(days=1)
    while not is_business_day(next_day):
        next_day += timedelta(days=1)
    return next_day
