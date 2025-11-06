from datetime import datetime, timedelta
from typing import List, Set


def calculate_easter(year: int) -> datetime:
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


def get_brazilian_fixed_holidays(year: int) -> List[datetime]:
    return [
        datetime(year, 1, 1),
        datetime(year, 4, 21),
        datetime(year, 5, 1),
        datetime(year, 9, 7),
        datetime(year, 10, 12),
        datetime(year, 11, 2),
        datetime(year, 11, 15),
        datetime(year, 11, 20),
        datetime(year, 12, 25),
    ]


def get_brazilian_variable_holidays(year: int) -> List[datetime]:
    easter = calculate_easter(year)
    
    return [
        easter - timedelta(days=47),
        easter - timedelta(days=46),
        easter - timedelta(days=2),
        easter + timedelta(days=60),
    ]


def get_all_brazilian_holidays(year: int) -> Set[datetime]:
    fixed = get_brazilian_fixed_holidays(year)
    variable = get_brazilian_variable_holidays(year)
    return set(fixed + variable)


def is_business_day(date: datetime) -> bool:
    if date.weekday() >= 5:
        return False
    
    holidays = get_all_brazilian_holidays(date.year)
    date_only = datetime(date.year, date.month, date.day)
    if date_only in holidays:
        return False
    
    return True


def count_business_days(start_date: datetime, end_date: datetime) -> int:
    if start_date > end_date:
        return 0
    
    count = 0
    current = start_date
    while current <= end_date:
        if is_business_day(current):
            count += 1
        current += timedelta(days=1)
    
    return count
