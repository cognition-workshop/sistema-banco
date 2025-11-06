from datetime import datetime, timedelta
from .models import BankingHoliday


def is_banking_day(date):
    """
    Check if a given date is a banking business day.
    Returns False for weekends and banking holidays.
    """
    if date.weekday() >= 5:
        return False
    
    if BankingHoliday.objects.filter(date=date).exists():
        return False
    
    return True


def next_banking_day(date):
    """
    Get the next banking business day after the given date.
    """
    next_day = date + timedelta(days=1)
    while not is_banking_day(next_day):
        next_day += timedelta(days=1)
    return next_day


def previous_banking_day(date):
    """
    Get the previous banking business day before the given date.
    """
    prev_day = date - timedelta(days=1)
    while not is_banking_day(prev_day):
        prev_day -= timedelta(days=1)
    return prev_day


def count_banking_days(start_date, end_date):
    """
    Count the number of banking business days between two dates (inclusive).
    """
    if start_date > end_date:
        return 0
    
    count = 0
    current_date = start_date
    while current_date <= end_date:
        if is_banking_day(current_date):
            count += 1
        current_date += timedelta(days=1)
    
    return count


def add_banking_days(date, days):
    """
    Add a number of banking business days to a date.
    """
    current_date = date
    days_added = 0
    
    while days_added < days:
        current_date += timedelta(days=1)
        if is_banking_day(current_date):
            days_added += 1
    
    return current_date
