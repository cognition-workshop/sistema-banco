from decimal import Decimal
from django.test import TestCase

from accounts.utils import calculate_compound_interest


class CalculateCompoundInterestTests(TestCase):
    """Test cases for the calculate_compound_interest utility function"""

    def test_basic_interest_calculation(self):
        """Test basic interest calculation with typical values"""
        principal = Decimal('1000.00')
        annual_rate = Decimal('5.00')
        calculations_per_year = 12
        
        interest = calculate_compound_interest(principal, annual_rate, calculations_per_year)
        
        self.assertEqual(interest, Decimal('4.17'))

    def test_different_calculation_frequencies(self):
        """Test interest calculation with different frequencies"""
        principal = Decimal('1000.00')
        annual_rate = Decimal('6.00')
        
        monthly_interest = calculate_compound_interest(principal, annual_rate, 12)
        self.assertEqual(monthly_interest, Decimal('5.00'))
        
        quarterly_interest = calculate_compound_interest(principal, annual_rate, 4)
        self.assertEqual(quarterly_interest, Decimal('15.00'))
        
        semiannual_interest = calculate_compound_interest(principal, annual_rate, 2)
        self.assertEqual(semiannual_interest, Decimal('30.00'))

    def test_zero_principal(self):
        """Test with zero principal balance"""
        interest = calculate_compound_interest(Decimal('0.00'), Decimal('5.00'), 12)
        self.assertEqual(interest, Decimal('0.00'))

    def test_zero_interest_rate(self):
        """Test with zero interest rate"""
        interest = calculate_compound_interest(Decimal('1000.00'), Decimal('0.00'), 12)
        self.assertEqual(interest, Decimal('0.00'))

    def test_rounding_to_two_decimals(self):
        """Test that result is properly rounded to 2 decimal places"""
        principal = Decimal('1000.00')
        annual_rate = Decimal('3.33')
        calculations_per_year = 12
        
        interest = calculate_compound_interest(principal, annual_rate, calculations_per_year)
        
        self.assertEqual(str(interest).split('.')[1].__len__(), 2)

    def test_high_interest_rate(self):
        """Test with high interest rate"""
        principal = Decimal('1000.00')
        annual_rate = Decimal('12.00')
        calculations_per_year = 12
        
        interest = calculate_compound_interest(principal, annual_rate, calculations_per_year)
        
        self.assertEqual(interest, Decimal('10.00'))

    def test_annual_calculation(self):
        """Test with annual calculation frequency (n=1)"""
        principal = Decimal('1000.00')
        annual_rate = Decimal('5.00')
        calculations_per_year = 1
        
        interest = calculate_compound_interest(principal, annual_rate, calculations_per_year)
        
        self.assertEqual(interest, Decimal('50.00'))

    def test_large_principal(self):
        """Test with large principal amount"""
        principal = Decimal('100000.00')
        annual_rate = Decimal('2.50')
        calculations_per_year = 6
        
        interest = calculate_compound_interest(principal, annual_rate, calculations_per_year)
        
        self.assertEqual(interest, Decimal('416.67'))
