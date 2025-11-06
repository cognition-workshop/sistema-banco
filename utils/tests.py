from django.test import TestCase
from datetime import datetime
from utils.brazilian_calendar import (
    calculate_easter,
    get_brazilian_fixed_holidays,
    get_brazilian_variable_holidays,
    get_all_brazilian_holidays,
    is_business_day,
    count_business_days,
)


class BrazilianCalendarTestCase(TestCase):
    
    def test_calculate_easter(self):
        easter_2024 = calculate_easter(2024)
        self.assertEqual(easter_2024.month, 3)
        self.assertEqual(easter_2024.day, 31)
        
        easter_2025 = calculate_easter(2025)
        self.assertEqual(easter_2025.month, 4)
        self.assertEqual(easter_2025.day, 20)
    
    def test_fixed_holidays_count(self):
        holidays = get_brazilian_fixed_holidays(2024)
        self.assertEqual(len(holidays), 9)
    
    def test_variable_holidays_count(self):
        holidays = get_brazilian_variable_holidays(2024)
        self.assertEqual(len(holidays), 4)
    
    def test_new_years_day_is_holiday(self):
        new_years = datetime(2024, 1, 1)
        self.assertFalse(is_business_day(new_years))
    
    def test_christmas_is_holiday(self):
        christmas = datetime(2024, 12, 25)
        self.assertFalse(is_business_day(christmas))
    
    def test_weekend_not_business_day(self):
        saturday = datetime(2024, 11, 2)
        sunday = datetime(2024, 11, 3)
        self.assertFalse(is_business_day(saturday))
        self.assertFalse(is_business_day(sunday))
    
    def test_regular_weekday_is_business_day(self):
        regular_day = datetime(2024, 11, 4)
        self.assertTrue(is_business_day(regular_day))
    
    def test_count_business_days(self):
        start = datetime(2024, 1, 1)
        end = datetime(2024, 1, 5)
        count = count_business_days(start, end)
        self.assertEqual(count, 4)
    
    def test_count_business_days_empty(self):
        start = datetime(2024, 1, 5)
        end = datetime(2024, 1, 1)
        count = count_business_days(start, end)
        self.assertEqual(count, 0)
