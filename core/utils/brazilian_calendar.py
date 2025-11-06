from datetime import datetime, timedelta
from dateutil.easter import easter


class BrazilianBankingCalendar:
    """Brazilian banking calendar with holidays."""
    
    @staticmethod
    def get_fixed_holidays(year):
        """Return fixed holidays for the year."""
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
    
    @staticmethod
    def get_movable_holidays(year):
        """Return movable holidays for the year (based on Easter)."""
        easter_date = easter(year)
        
        carnaval = easter_date - timedelta(days=47)
        good_friday = easter_date - timedelta(days=2)
        corpus_christi = easter_date + timedelta(days=60)
        
        return [carnaval, good_friday, corpus_christi]
    
    @classmethod
    def get_all_holidays(cls, year):
        """Get all holidays for the year."""
        fixed = cls.get_fixed_holidays(year)
        movable = cls.get_movable_holidays(year)
        return fixed + movable
    
    @classmethod
    def is_business_day(cls, date):
        """Check if date is a business day."""
        from datetime import datetime, date as date_class
        
        if isinstance(date, datetime):
            check_date = date.date()
        else:
            check_date = date
        
        if check_date.weekday() >= 5:
            return False
        
        holidays = cls.get_all_holidays(check_date.year)
        holiday_dates = [h.date() if isinstance(h, datetime) else h for h in holidays]
        return check_date not in holiday_dates
    
    @classmethod
    def next_business_day(cls, date):
        """Get next business day."""
        next_day = date + timedelta(days=1)
        while not cls.is_business_day(next_day):
            next_day += timedelta(days=1)
        return next_day
