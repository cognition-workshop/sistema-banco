from datetime import datetime, timedelta
from typing import List


def easter_date(year: int) -> datetime:
    """Calculate Easter date using Meeus/Jones/Butcher algorithm"""
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return datetime(year, month, day)


def get_brazilian_holidays(year: int) -> List[datetime]:
    """Get all Brazilian national banking holidays for a given year"""
    holidays = []
    
    holidays.append(datetime(year, 1, 1))
    holidays.append(datetime(year, 4, 21))
    holidays.append(datetime(year, 5, 1))
    holidays.append(datetime(year, 9, 7))
    holidays.append(datetime(year, 10, 12))
    holidays.append(datetime(year, 11, 2))
    holidays.append(datetime(year, 11, 15))
    holidays.append(datetime(year, 12, 25))
    
    easter = easter_date(year)
    
    carnaval = easter - timedelta(days=47)
    holidays.append(carnaval)
    
    good_friday = easter - timedelta(days=2)
    holidays.append(good_friday)
    
    corpus_christi = easter + timedelta(days=60)
    holidays.append(corpus_christi)
    
    return sorted(holidays)


def is_business_day(date: datetime) -> bool:
    """Check if a date is a banking business day in Brazil"""
    if date.weekday() >= 5:
        return False
    
    holidays = get_brazilian_holidays(date.year)
    date_normalized = datetime(date.year, date.month, date.day)
    
    return date_normalized not in holidays


def next_business_day(date: datetime) -> datetime:
    """Get the next banking business day"""
    next_day = date + timedelta(days=1)
    while not is_business_day(next_day):
        next_day += timedelta(days=1)
    return next_day


def previous_business_day(date: datetime) -> datetime:
    """Get the previous banking business day"""
    prev_day = date - timedelta(days=1)
    while not is_business_day(prev_day):
        prev_day -= timedelta(days=1)
    return prev_day


def count_business_days(start_date: datetime, end_date: datetime) -> int:
    """Count business days between two dates (inclusive)"""
    if start_date > end_date:
        return 0
    
    count = 0
    current = start_date
    while current <= end_date:
        if is_business_day(current):
            count += 1
        current += timedelta(days=1)
    
    return count
