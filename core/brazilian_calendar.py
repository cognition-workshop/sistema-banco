from datetime import datetime, timedelta, date
from workalendar.america import Brazil


class BrazilianBankingCalendar:
    def __init__(self):
        self.brazil_calendar = Brazil()
    
    def is_business_day(self, check_date):
        if isinstance(check_date, datetime):
            check_date = check_date.date()
        
        return self.brazil_calendar.is_working_day(check_date)
    
    def next_business_day(self, start_date):
        if isinstance(start_date, datetime):
            start_date = start_date.date()
        
        next_day = start_date + timedelta(days=1)
        while not self.is_business_day(next_day):
            next_day += timedelta(days=1)
        return next_day
    
    def add_business_days(self, start_date, days):
        if isinstance(start_date, datetime):
            start_date = start_date.date()
        
        current_date = start_date
        days_added = 0
        
        while days_added < days:
            current_date += timedelta(days=1)
            if self.is_business_day(current_date):
                days_added += 1
        
        return current_date
    
    def get_brazilian_holidays(self, year):
        return self.brazil_calendar.holidays(year)
    
    def is_banking_hours(self, check_datetime):
        from django.conf import settings
        
        if not isinstance(check_datetime, datetime):
            return False
        
        banking_start = getattr(settings, 'BANKING_HOURS_START', 10)
        banking_end = getattr(settings, 'BANKING_HOURS_END', 16)
        
        if not self.is_business_day(check_datetime.date()):
            return False
        
        hour = check_datetime.hour
        return banking_start <= hour < banking_end
