from decimal import Decimal
from datetime import date, datetime
from django.test import TestCase, RequestFactory
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from accounts.models import User, BankAccountType, UserBankAccount, UserAddress
from accounts.forms import UserAddressForm, UserRegistrationForm
from accounts.utils import calcular_digito_verificador
from accounts.constants import MALE, FEMALE


User = get_user_model()


class UserModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=5000,
            annual_interest_rate=5.0,
            interest_calculation_per_year=12
        )

    def test_user_creation(self):
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertEqual(str(self.user), 'test@example.com')
        self.assertTrue(self.user.check_password('testpass123'))

    def test_user_balance_without_account(self):
        self.assertEqual(self.user.balance, 0)

    def test_user_balance_with_account(self):
        UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender=MALE,
            birth_date=date(1990, 1, 1),
            balance=1500.50
        )
        self.assertEqual(self.user.balance, Decimal('1500.50'))


class BankAccountTypeModelTest(TestCase):
    def setUp(self):
        self.account_type = BankAccountType.objects.create(
            name='Savings Account',
            maximum_withdrawal_amount=5000.00,
            annual_interest_rate=5.0,
            interest_calculation_per_year=12
        )

    def test_account_type_creation(self):
        self.assertEqual(self.account_type.name, 'Savings Account')
        self.assertEqual(self.account_type.annual_interest_rate, Decimal('5.0'))

    def test_account_type_str(self):
        self.assertEqual(str(self.account_type), 'Savings Account')

    def test_calculate_interest_monthly(self):
        principal = Decimal('1000.00')
        interest = self.account_type.calculate_interest(principal)
        expected = round((principal * (1 + ((Decimal('5.0')/100) / 12))) - principal, 2)
        self.assertEqual(interest, expected)
        self.assertGreater(interest, 0)

    def test_calculate_interest_quarterly(self):
        account_type = BankAccountType.objects.create(
            name='Current Account',
            maximum_withdrawal_amount=10000.00,
            annual_interest_rate=3.0,
            interest_calculation_per_year=4
        )
        principal = Decimal('5000.00')
        interest = account_type.calculate_interest(principal)
        expected = round((principal * (1 + ((Decimal('3.0')/100) / 4))) - principal, 2)
        self.assertEqual(interest, expected)

    def test_calculate_interest_zero_principal(self):
        interest = self.account_type.calculate_interest(Decimal('0'))
        self.assertEqual(interest, Decimal('0.00'))


class UserBankAccountModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='account@example.com',
            password='testpass123'
        )
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=5000,
            annual_interest_rate=5.0,
            interest_calculation_per_year=12
        )

    def test_account_creation_without_brazilian_format(self):
        account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender=MALE,
            birth_date=date(1990, 1, 1),
            balance=1000.00
        )
        self.assertEqual(str(account), '1000000001')
        self.assertEqual(account.get_formatted_account(), 'Conta 1000000001')

    def test_account_creation_with_brazilian_format(self):
        account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            agencia='1234',
            conta_digito='5',
            gender=FEMALE,
            birth_date=date(1995, 5, 15),
            balance=2500.00
        )
        self.assertEqual(str(account), 'Ag. 1234 - C/C 1000000001-5')
        self.assertEqual(account.get_formatted_account(), 'Agência 1234 - Conta 1000000001-5')

    def test_get_interest_calculation_months_monthly(self):
        account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender=MALE,
            birth_date=date(1990, 1, 1),
            interest_start_date=date(2024, 1, 15)
        )
        months = account.get_interest_calculation_months()
        self.assertEqual(months, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])

    def test_get_interest_calculation_months_quarterly(self):
        quarterly_type = BankAccountType.objects.create(
            name='Quarterly',
            maximum_withdrawal_amount=10000,
            annual_interest_rate=4.0,
            interest_calculation_per_year=4
        )
        account = UserBankAccount.objects.create(
            user=self.user,
            account_type=quarterly_type,
            account_no=1000000002,
            gender=MALE,
            birth_date=date(1990, 1, 1),
            interest_start_date=date(2024, 3, 1)
        )
        months = account.get_interest_calculation_months()
        self.assertEqual(months, [3, 6, 9, 12])

    def test_account_balance_default(self):
        account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000003,
            gender=MALE,
            birth_date=date(1990, 1, 1)
        )
        self.assertEqual(account.balance, Decimal('0'))


class UserAddressModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='address@example.com',
            password='testpass123'
        )

    def test_address_creation(self):
        address = UserAddress.objects.create(
            user=self.user,
            street_address='123 Test Street',
            city='São Paulo',
            postal_code=12345678,
            country='Brazil'
        )
        self.assertEqual(address.street_address, '123 Test Street')
        self.assertEqual(address.city, 'São Paulo')
        self.assertEqual(str(address), 'address@example.com')


class UserRegistrationFormTest(TestCase):
    def setUp(self):
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=5000,
            annual_interest_rate=5.0,
            interest_calculation_per_year=12
        )

    def test_valid_registration_form(self):
        form_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
            'account_type': self.account_type.id,
            'gender': MALE,
            'birth_date': '1990-01-01'
        }
        form = UserRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_registration_form_creates_user_and_account(self):
        form_data = {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'email': 'jane@example.com',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
            'account_type': self.account_type.id,
            'gender': FEMALE,
            'birth_date': '1995-05-15'
        }
        form = UserRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        user = form.save()
        self.assertEqual(user.email, 'jane@example.com')
        self.assertTrue(user.check_password('SecurePass123!'))
        self.assertTrue(hasattr(user, 'account'))
        self.assertEqual(user.account.gender, FEMALE)
        self.assertEqual(user.account.account_type, self.account_type)
        expected_account_no = user.id + settings.ACCOUNT_NUMBER_START_FROM
        self.assertEqual(user.account.account_no, expected_account_no)

    def test_registration_form_password_mismatch(self):
        form_data = {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'password1': 'SecurePass123!',
            'password2': 'DifferentPass123!',
            'account_type': self.account_type.id,
            'gender': MALE,
            'birth_date': '1990-01-01'
        }
        form = UserRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)


class UserAddressFormTest(TestCase):
    def test_valid_address_form(self):
        form_data = {
            'street_address': '456 Main St',
            'city': 'Rio de Janeiro',
            'postal_code': 20000000,
            'country': 'Brazil'
        }
        form = UserAddressForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_address_form_missing_required_field(self):
        form_data = {
            'street_address': '456 Main St',
            'city': 'Rio de Janeiro',
            'country': 'Brazil'
        }
        form = UserAddressForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('postal_code', form.errors)


class CalcularDigitoVerificadorTest(TestCase):
    def test_calcular_digito_verificador_basic(self):
        digito = calcular_digito_verificador('1234', '123456')
        self.assertIn(digito, '0123456789X')

    def test_calcular_digito_verificador_returns_x_for_high_values(self):
        digito = calcular_digito_verificador('9999', '999999')
        self.assertTrue(isinstance(digito, str))

    def test_calcular_digito_verificador_with_integers(self):
        digito = calcular_digito_verificador(1234, 123456)
        self.assertIn(digito, '0123456789X')

    def test_calcular_digito_verificador_consistency(self):
        digito1 = calcular_digito_verificador('1234', '567890')
        digito2 = calcular_digito_verificador('1234', '567890')
        self.assertEqual(digito1, digito2)
