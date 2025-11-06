from decimal import Decimal
from datetime import date
from django.test import TestCase
from django.contrib.auth import get_user_model

from accounts.models import BankAccountType, UserBankAccount
from accounts.constants import MALE

User = get_user_model()


class UserModelTests(TestCase):
    def setUp(self):
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('5.00'),
            interest_calculation_per_year=12
        )
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )

    def test_user_balance_returns_account_balance_when_account_exists(self):
        UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender=MALE,
            balance=Decimal('1500.50')
        )
        self.assertEqual(self.user.balance, Decimal('1500.50'))

    def test_user_balance_returns_zero_when_no_account(self):
        self.assertEqual(self.user.balance, 0)


class BankAccountTypeModelTests(TestCase):
    def setUp(self):
        self.savings_account = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('6.00'),
            interest_calculation_per_year=12
        )
        self.current_account = BankAccountType.objects.create(
            name='Current',
            maximum_withdrawal_amount=Decimal('10000.00'),
            annual_interest_rate=Decimal('4.00'),
            interest_calculation_per_year=4
        )

    def test_calculate_interest_monthly_compounding(self):
        principal = Decimal('1000.00')
        interest = self.savings_account.calculate_interest(principal)
        expected = round((principal * (1 + (Decimal('6.00')/100) / 12)) - principal, 2)
        self.assertEqual(interest, expected)

    def test_calculate_interest_quarterly_compounding(self):
        principal = Decimal('5000.00')
        interest = self.current_account.calculate_interest(principal)
        expected = round((principal * (1 + (Decimal('4.00')/100) / 4)) - principal, 2)
        self.assertEqual(interest, expected)

    def test_calculate_interest_returns_decimal_with_two_places(self):
        principal = Decimal('1234.56')
        interest = self.savings_account.calculate_interest(principal)
        self.assertEqual(interest, round(interest, 2))


class UserBankAccountModelTests(TestCase):
    def setUp(self):
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('5.00'),
            interest_calculation_per_year=4
        )
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.bank_account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender=MALE,
            interest_start_date=date(2024, 3, 1)
        )

    def test_get_interest_calculation_months_quarterly(self):
        months = self.bank_account.get_interest_calculation_months()
        self.assertEqual(months, [3, 6, 9, 12])

    def test_get_interest_calculation_months_monthly(self):
        self.account_type.interest_calculation_per_year = 12
        self.account_type.save()
        self.bank_account.interest_start_date = date(2024, 1, 1)
        self.bank_account.save()
        months = self.bank_account.get_interest_calculation_months()
        self.assertEqual(months, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])

    def test_get_interest_calculation_months_biannually(self):
        self.account_type.interest_calculation_per_year = 2
        self.account_type.save()
        self.bank_account.interest_start_date = date(2024, 6, 1)
        self.bank_account.save()
        months = self.bank_account.get_interest_calculation_months()
        self.assertEqual(months, [6, 12])
