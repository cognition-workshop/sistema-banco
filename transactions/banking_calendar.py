from datetime import date, timedelta
from typing import List


class BrazilianBankingCalendar:
    """
    Brazilian banking calendar with national and banking holidays
    """
    
    @staticmethod
    def get_fixed_holidays(year: int) -> List[date]:
        """Returns fixed Brazilian national holidays"""
        return [
            date(year, 1, 1),
            date(year, 4, 21),
            date(year, 5, 1),
            date(year, 9, 7),
            date(year, 10, 12),
            date(year, 11, 2),
            date(year, 11, 15),
            date(year, 12, 25),
        ]
    
    @staticmethod
    def get_moveable_holidays(year: int) -> List[date]:
        """
        Returns moveable holidays (Carnival, Good Friday, Corpus Christi)
        """
        return []
    
    @classmethod
    def is_banking_holiday(cls, check_date: date) -> bool:
        """Check if date is a banking holiday"""
        year = check_date.year
        holidays = cls.get_fixed_holidays(year) + cls.get_moveable_holidays(year)
        return check_date in holidays
    
    @classmethod
    def is_business_day(cls, check_date: date) -> bool:
        """Check if date is a business day (not weekend or holiday)"""
        if check_date.weekday() >= 5:
            return False
        return not cls.is_banking_holiday(check_date)
    
    @classmethod
    def get_next_business_day(cls, check_date: date) -> date:
        """Get next business day after given date"""
        next_day = check_date + timedelta(days=1)
        while not cls.is_business_day(next_day):
            next_day += timedelta(days=1)
        return next_day
    
    @classmethod
    def count_business_days(cls, start_date: date, end_date: date) -> int:
        """Count business days between two dates (inclusive)"""
        count = 0
        current = start_date
        while current <= end_date:
            if cls.is_business_day(current):
                count += 1
            current += timedelta(days=1)
        return count
