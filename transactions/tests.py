from django.test import TestCase
from decimal import Decimal
from accounts.models import BankAccountType


class InterestCalculationTestCase(TestCase):
    
    def setUp(self):
        self.account_type = BankAccountType.objects.create(
            name='Test Savings',
            maximum_withdrawal_amount=Decimal('10000.00'),
            annual_interest_rate=Decimal('6.00'),
            interest_calculation_per_year=12
        )
    
    def test_calculate_interest_full_period(self):
        principal = Decimal('1000.00')
        interest = self.account_type.calculate_interest(principal, business_days_ratio=1.0)
        self.assertEqual(interest, Decimal('5.00'))
    
    def test_calculate_interest_partial_period(self):
        principal = Decimal('1000.00')
        interest = self.account_type.calculate_interest(principal, business_days_ratio=0.952)
        self.assertEqual(interest, Decimal('4.76'))
    
    def test_calculate_interest_reduced_period(self):
        principal = Decimal('1000.00')
        interest = self.account_type.calculate_interest(principal, business_days_ratio=0.857)
        self.assertEqual(interest, Decimal('4.28'))
    
    def test_calculate_interest_default_ratio(self):
        principal = Decimal('1000.00')
        interest_with_default = self.account_type.calculate_interest(principal)
        interest_with_explicit = self.account_type.calculate_interest(principal, business_days_ratio=1.0)
        self.assertEqual(interest_with_default, interest_with_explicit)
    
    def test_calculate_interest_zero_principal(self):
        principal = Decimal('0.00')
        interest = self.account_type.calculate_interest(principal, business_days_ratio=1.0)
        self.assertEqual(interest, Decimal('0.00'))
