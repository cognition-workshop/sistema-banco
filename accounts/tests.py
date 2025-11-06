from django.test import TestCase
from django.core.exceptions import ValidationError
from accounts.validators import validate_cpf, format_cpf
from accounts.managers import generate_account_number
from core.utils.brazilian_calendar import BrazilianBankingCalendar
from datetime import datetime


class CPFValidatorTest(TestCase):
    def test_valid_cpf(self):
        """Test valid CPF validation"""
        try:
            validate_cpf('12345678909')
            validate_cpf('123.456.789-09')
        except ValidationError:
            self.fail("Valid CPF should not raise ValidationError")
    
    def test_invalid_cpf_wrong_digits(self):
        """Test invalid CPF with wrong check digits"""
        with self.assertRaises(ValidationError):
            validate_cpf('12345678900')
    
    def test_invalid_cpf_all_same(self):
        """Test invalid CPF with all same digits"""
        with self.assertRaises(ValidationError):
            validate_cpf('11111111111')
    
    def test_format_cpf(self):
        """Test CPF formatting"""
        self.assertEqual(format_cpf('12345678909'), '123.456.789-09')
        self.assertEqual(format_cpf('123.456.789-09'), '123.456.789-09')


class BrazilianCalendarTest(TestCase):
    def test_is_business_day_weekday(self):
        """Test business day detection for weekdays"""
        weekday = datetime(2024, 11, 6)
        self.assertTrue(BrazilianBankingCalendar.is_business_day(weekday))
    
    def test_is_business_day_weekend(self):
        """Test business day detection for weekends"""
        saturday = datetime(2024, 11, 9)
        sunday = datetime(2024, 11, 10)
        self.assertFalse(BrazilianBankingCalendar.is_business_day(saturday))
        self.assertFalse(BrazilianBankingCalendar.is_business_day(sunday))
    
    def test_get_all_holidays(self):
        """Test holiday list generation"""
        holidays = BrazilianBankingCalendar.get_all_holidays(2024)
        self.assertGreater(len(holidays), 0)
        self.assertIn(datetime(2024, 1, 1), holidays)
        self.assertIn(datetime(2024, 12, 25), holidays)


class AccountNumberGenerationTest(TestCase):
    def test_generate_account_number_format(self):
        """Test account number generation format"""
        agency, account_number, digit = generate_account_number()
        self.assertEqual(len(agency), 4)
        self.assertEqual(len(account_number), 7)
        self.assertEqual(len(digit), 1)
