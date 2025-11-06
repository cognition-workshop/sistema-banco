from decimal import Decimal
from datetime import date

from django.test import TestCase

from accounts.models import User, BankAccountType, UserBankAccount
from accounts.constants import MALE


class BankAccountTypeModelTest(TestCase):
    
    def setUp(self):
        self.savings_type = BankAccountType.objects.create(
            name="Savings Account",
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('5.00'),
            interest_calculation_per_year=12
        )
    
    def test_calculate_interest_with_positive_principal(self):
        principal = Decimal('1000.00')
        interest = self.savings_type.calculate_interest(principal)
        self.assertEqual(interest, Decimal('4.17'))
    
    def test_calculate_interest_with_zero_principal(self):
        interest = self.savings_type.calculate_interest(Decimal('0'))
        self.assertEqual(interest, Decimal('0.00'))
    
    def test_calculate_interest_with_different_rate(self):
        account_type = BankAccountType.objects.create(
            name="Current",
            maximum_withdrawal_amount=Decimal('10000.00'),
            annual_interest_rate=Decimal('2.50'),
            interest_calculation_per_year=6
        )
        principal = Decimal('1000.00')
        interest = account_type.calculate_interest(principal)
        self.assertEqual(interest, Decimal('4.17'))


class UserBankAccountModelTest(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.account_type = BankAccountType.objects.create(
            name="Savings",
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('5.00'),
            interest_calculation_per_year=12
        )
    
    def test_get_interest_calculation_months_monthly(self):
        account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1001,
            gender=MALE,
            interest_start_date=date(2024, 1, 15)
        )
        months = account.get_interest_calculation_months()
        self.assertEqual(months, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])
    
    def test_get_interest_calculation_months_quarterly(self):
        account_type = BankAccountType.objects.create(
            name="Quarterly",
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('5.00'),
            interest_calculation_per_year=4
        )
        account = UserBankAccount.objects.create(
            user=self.user,
            account_type=account_type,
            account_no=1002,
            gender=MALE,
            interest_start_date=date(2024, 3, 15)
        )
        months = account.get_interest_calculation_months()
        self.assertEqual(months, [3, 6, 9, 12])


class UserModelTest(TestCase):
    
    def test_balance_property_with_account(self):
        user = User.objects.create_user(email='test@example.com', password='test123')
        account_type = BankAccountType.objects.create(
            name="Savings",
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('5.00'),
            interest_calculation_per_year=12
        )
        UserBankAccount.objects.create(
            user=user,
            account_type=account_type,
            account_no=1001,
            gender=MALE,
            balance=Decimal('1500.50')
        )
        self.assertEqual(user.balance, Decimal('1500.50'))
    
    def test_balance_property_without_account(self):
        user = User.objects.create_user(email='test@example.com', password='test123')
        self.assertEqual(user.balance, 0)
