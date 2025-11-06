from decimal import Decimal
from datetime import date, datetime
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.conf import settings

from accounts.models import BankAccountType, UserBankAccount, UserAddress
from accounts.forms import UserRegistrationForm, UserAddressForm

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
            password='testpass123',
            first_name='Test',
            last_name='User'
        )

    def test_user_balance_with_account(self):
        UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender='M',
            balance=Decimal('1500.50')
        )
        self.assertEqual(self.user.balance, Decimal('1500.50'))

    def test_user_balance_without_account(self):
        self.assertEqual(self.user.balance, 0)

    def test_user_string_representation(self):
        self.assertEqual(str(self.user), 'test@example.com')


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

    def test_calculate_interest_monthly(self):
        principal = Decimal('1000.00')
        interest = self.savings_account.calculate_interest(principal)
        expected_interest = (principal * (1 + ((Decimal('6.00')/100) / 12))) - principal
        self.assertEqual(interest, round(expected_interest, 2))

    def test_calculate_interest_quarterly(self):
        principal = Decimal('2000.00')
        interest = self.current_account.calculate_interest(principal)
        expected_interest = (principal * (1 + ((Decimal('4.00')/100) / 4))) - principal
        self.assertEqual(interest, round(expected_interest, 2))

    def test_calculate_interest_zero_principal(self):
        interest = self.savings_account.calculate_interest(Decimal('0.00'))
        self.assertEqual(interest, Decimal('0.00'))


class UserBankAccountModelTests(TestCase):
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
        self.bank_account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender='M',
            balance=Decimal('1000.00'),
            interest_start_date=date(2024, 3, 1)
        )

    def test_get_interest_calculation_months_monthly(self):
        months = self.bank_account.get_interest_calculation_months()
        self.assertEqual(months, [3, 4, 5, 6, 7, 8, 9, 10, 11, 12])

    def test_get_interest_calculation_months_quarterly(self):
        quarterly_account_type = BankAccountType.objects.create(
            name='Quarterly',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('5.00'),
            interest_calculation_per_year=4
        )
        bank_account = UserBankAccount.objects.create(
            user=User.objects.create_user(email='quarterly@example.com', password='test'),
            account_type=quarterly_account_type,
            account_no=1000000002,
            gender='F',
            interest_start_date=date(2024, 2, 1)
        )
        months = bank_account.get_interest_calculation_months()
        self.assertEqual(months, [2, 5, 8, 11])

    def test_bank_account_string_representation(self):
        self.assertEqual(str(self.bank_account), '1000000001')


class UserRegistrationFormTests(TestCase):
    def setUp(self):
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('5.00'),
            interest_calculation_per_year=12
        )

    def test_user_registration_form_creates_user_and_account(self):
        form_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
            'account_type': self.account_type.id,
            'gender': 'M',
            'birth_date': '1990-01-01'
        }
        form = UserRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        user = form.save()
        self.assertEqual(user.email, 'john.doe@example.com')
        self.assertEqual(user.first_name, 'John')
        self.assertTrue(user.check_password('SecurePass123!'))
        
        self.assertTrue(hasattr(user, 'account'))
        self.assertEqual(user.account.account_type, self.account_type)
        self.assertEqual(user.account.gender, 'M')
        self.assertEqual(
            user.account.account_no,
            user.id + settings.ACCOUNT_NUMBER_START_FROM
        )

    def test_user_registration_form_invalid_without_required_fields(self):
        form_data = {
            'email': 'incomplete@example.com',
        }
        form = UserRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
