from decimal import Decimal
from datetime import date
from django.test import TestCase
from django.contrib.auth import get_user_model

from accounts.models import User, BankAccountType, UserBankAccount
from accounts.constants import MALE

User = get_user_model()


class UserModelTests(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('5.00'),
            interest_calculation_per_year=12
        )
    
    def test_user_balance_with_account(self):
        UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender=MALE,
            balance=Decimal('1500.50')
        )
        self.assertEqual(self.user.balance, Decimal('1500.50'))
    
    def test_user_balance_without_account(self):
        self.assertEqual(self.user.balance, 0)


class BankAccountTypeModelTests(TestCase):
    
    def test_calculate_interest_basic(self):
        account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('5.00'),
            interest_calculation_per_year=12
        )
        principal = Decimal('1000.00')
        interest = account_type.calculate_interest(principal)
        self.assertEqual(interest, Decimal('4.17'))
    
    def test_calculate_interest_zero_principal(self):
        account_type = BankAccountType.objects.create(
            name='Checking',
            maximum_withdrawal_amount=Decimal('10000.00'),
            annual_interest_rate=Decimal('3.00'),
            interest_calculation_per_year=4
        )
        interest = account_type.calculate_interest(Decimal('0'))
        self.assertEqual(interest, Decimal('0.00'))


class UserBankAccountModelTests(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='account@example.com',
            password='testpass123'
        )
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('5.00'),
            interest_calculation_per_year=4
        )
    
    def test_create_user_bank_account(self):
        account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender=MALE,
            birth_date=date(1990, 1, 1),
            balance=Decimal('500.00'),
            interest_start_date=date(2024, 3, 1),
            initial_deposit_date=date(2024, 1, 1)
        )
        self.assertEqual(account.user, self.user)
        self.assertEqual(account.account_no, 1000000001)
        self.assertEqual(account.balance, Decimal('500.00'))
    
    def test_get_interest_calculation_months(self):
        account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000002,
            gender=MALE,
            interest_start_date=date(2024, 2, 1)
        )
        months = account.get_interest_calculation_months()
        self.assertEqual(months, [2, 5, 8, 11])
