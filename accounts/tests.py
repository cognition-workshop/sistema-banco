from decimal import Decimal
from django.test import TestCase
from accounts.utils import calculate_compound_interest


class CalculateCompoundInterestTests(TestCase):
    """Tests for the calculate_compound_interest utility function"""
    
    def test_calculate_interest_savings_account(self):
        """Test interest calculation for Savings Account (5% annual, 12x/year)"""
        principal = Decimal('5000.00')
        annual_rate = Decimal('5.00')
        frequency = 12
        
        interest = calculate_compound_interest(principal, annual_rate, frequency)
        
        self.assertEqual(interest, Decimal('20.83'))
    
    def test_calculate_interest_current_account(self):
        """Test interest calculation for Current Account (2.5% annual, 6x/year)"""
        principal = Decimal('10000.00')
        annual_rate = Decimal('2.50')
        frequency = 6
        
        interest = calculate_compound_interest(principal, annual_rate, frequency)
        
        self.assertEqual(interest, Decimal('41.67'))
    
    def test_calculate_interest_with_small_amount(self):
        """Test interest calculation with small principal amount"""
        principal = Decimal('100.00')
        annual_rate = Decimal('3.00')
        frequency = 12
        
        interest = calculate_compound_interest(principal, annual_rate, frequency)
        
        self.assertEqual(interest, Decimal('0.25'))
    
    def test_calculate_interest_with_zero_balance(self):
        """Test that zero balance results in zero interest"""
        principal = Decimal('0.00')
        annual_rate = Decimal('5.00')
        frequency = 12
        
        interest = calculate_compound_interest(principal, annual_rate, frequency)
        
        self.assertEqual(interest, Decimal('0.00'))
    
    def test_calculate_interest_with_zero_rate(self):
        """Test that zero interest rate results in zero interest"""
        principal = Decimal('5000.00')
        annual_rate = Decimal('0.00')
        frequency = 12
        
        interest = calculate_compound_interest(principal, annual_rate, frequency)
        
        self.assertEqual(interest, Decimal('0.00'))
    
    def test_rounding_to_two_decimal_places(self):
        """Test that result is properly rounded to 2 decimal places"""
        principal = Decimal('1000.00')
        annual_rate = Decimal('3.333')
        frequency = 12
        
        interest = calculate_compound_interest(principal, annual_rate, frequency)
        
        self.assertEqual(len(str(interest).split('.')[-1]), 2)
    
    def test_calculate_interest_high_frequency(self):
        """Test interest calculation with maximum frequency (12x/year)"""
        principal = Decimal('15000.00')
        annual_rate = Decimal('4.50')
        frequency = 12
        
        interest = calculate_compound_interest(principal, annual_rate, frequency)
        
        self.assertEqual(interest, Decimal('56.25'))
    
    def test_calculate_interest_low_frequency(self):
        """Test interest calculation with minimum frequency (1x/year)"""
        principal = Decimal('8000.00')
        annual_rate = Decimal('6.00')
        frequency = 1
        
        interest = calculate_compound_interest(principal, annual_rate, frequency)
        
        self.assertEqual(interest, Decimal('480.00'))
