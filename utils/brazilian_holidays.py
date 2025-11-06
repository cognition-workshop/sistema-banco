from datetime import datetime, timedelta
from workalendar.america import Brazil


def is_business_day(date=None):
    if date is None:
        date = datetime.now().date()
    elif isinstance(date, datetime):
        date = date.date()
    
    calendar = Brazil()
    return calendar.is_working_day(date)


def get_next_business_day(date=None):
    if date is None:
        date = datetime.now().date()
    elif isinstance(date, datetime):
        date = date.date()
    
    calendar = Brazil()
    next_day = date
    while not calendar.is_working_day(next_day):
        next_day += timedelta(days=1)
    return next_day


def get_brazilian_holidays(year=None):
    if year is None:
        year = datetime.now().year
    
    calendar = Brazil()
    return calendar.holidays(year)
