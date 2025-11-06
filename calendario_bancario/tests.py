from django.test import TestCase
from datetime import date
from calendario_bancario.models import FeriadoBancario
from calendario_bancario.utils import is_dia_util


class BusinessDayTests(TestCase):
    def test_weekend_not_business_day(self):
        """Test that weekends are not business days"""
        saturday = date(2024, 11, 9)
        self.assertFalse(is_dia_util(saturday))
        
        sunday = date(2024, 11, 10)
        self.assertFalse(is_dia_util(sunday))
    
    def test_holiday_not_business_day(self):
        """Test that holidays are not business days"""
        holiday = date(2024, 12, 25)
        FeriadoBancario.objects.create(
            data=holiday,
            nome='Natal',
            tipo='NACIONAL',
            ativo=True
        )
        self.assertFalse(is_dia_util(holiday))
    
    def test_regular_day_is_business_day(self):
        """Test that regular weekdays are business days"""
        monday = date(2024, 11, 11)
        self.assertTrue(is_dia_util(monday))
