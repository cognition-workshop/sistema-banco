from datetime import date, timedelta
from django.utils import timezone

def brazilian_holidays(year):
    """Return list of Brazilian federal holidays for given year"""
    holidays = []
    
    holidays.append(date(year, 1, 1))
    holidays.append(date(year, 4, 21))
    holidays.append(date(year, 5, 1))
    holidays.append(date(year, 9, 7))
    holidays.append(date(year, 10, 12))
    holidays.append(date(year, 11, 2))
    holidays.append(date(year, 11, 15))
    holidays.append(date(year, 12, 25))
    
    holidays.append(date(year, 2, 13))
    holidays.append(date(year, 3, 29))
    holidays.append(date(year, 5, 30))
    
    return holidays


def is_business_day(check_date):
    """Check if given date is a banking business day in Brazil"""
    if check_date.weekday() >= 5:
        return False
    
    year_holidays = brazilian_holidays(check_date.year)
    if check_date in year_holidays:
        return False
    
    return True


def next_business_day(start_date=None):
    """Return next business day after given date"""
    if start_date is None:
        start_date = timezone.now().date()
    
    next_day = start_date + timedelta(days=1)
    while not is_business_day(next_day):
        next_day += timedelta(days=1)
    
    return next_day


def previous_business_day(start_date=None):
    """Return previous business day before given date"""
    if start_date is None:
        start_date = timezone.now().date()
    
    prev_day = start_date - timedelta(days=1)
    while not is_business_day(prev_day):
        prev_day -= timedelta(days=1)
    
    return prev_day


def count_business_days(start_date, end_date):
    """Count business days between two dates (inclusive)"""
    count = 0
    current = start_date
    
    while current <= end_date:
        if is_business_day(current):
            count += 1
        current += timedelta(days=1)
    
    return count
