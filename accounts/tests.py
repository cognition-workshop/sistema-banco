from decimal import Decimal
from datetime import date
from django.test import TestCase
from django.conf import settings
from django.contrib.auth import get_user_model

from accounts.models import (
    User,
    BankAccountType,
    UserBankAccount,
    UserAddress
)
from accounts.forms import UserRegistrationForm, UserAddressForm
from accounts.constants import GENDER_CHOICE


class TestUserModel(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
    
    def test_user_creation(self):
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertEqual(self.user.first_name, 'Test')
        self.assertEqual(self.user.last_name, 'User')
        self.assertTrue(self.user.check_password('testpass123'))
    
    def test_user_string_representation(self):
        self.assertEqual(str(self.user), 'test@example.com')
    
    def test_user_email_is_username(self):
        self.assertEqual(User.USERNAME_FIELD, 'email')
    
    def test_user_balance_with_account(self):
        account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=5000,
            annual_interest_rate=5,
            interest_calculation_per_year=12
        )
        account = UserBankAccount.objects.create(
            user=self.user,
            account_type=account_type,
            account_no=1000000001,
            gender='M',
            balance=Decimal('1000.50')
        )
        self.assertEqual(self.user.balance, Decimal('1000.50'))
    
    def test_user_balance_without_account(self):
        self.assertEqual(self.user.balance, 0)
    
    def test_email_uniqueness(self):
        with self.assertRaises(Exception):
            User.objects.create_user(
                email='test@example.com',
                password='testpass456'
            )


class TestBankAccountTypeModel(TestCase):
    
    def setUp(self):
        self.savings_account = BankAccountType.objects.create(
            name='Savings Account',
            maximum_withdrawal_amount=5000,
            annual_interest_rate=5,
            interest_calculation_per_year=12
        )
        self.current_account = BankAccountType.objects.create(
            name='Current Account',
            maximum_withdrawal_amount=10000,
            annual_interest_rate=3.5,
            interest_calculation_per_year=4
        )
    
    def test_account_type_creation(self):
        self.assertEqual(self.savings_account.name, 'Savings Account')
        self.assertEqual(self.savings_account.maximum_withdrawal_amount, 5000)
        self.assertEqual(self.savings_account.annual_interest_rate, 5)
        self.assertEqual(self.savings_account.interest_calculation_per_year, 12)
    
    def test_account_type_string_representation(self):
        self.assertEqual(str(self.savings_account), 'Savings Account')
    
    def test_calculate_interest_with_5_percent_monthly(self):
        principal = Decimal('1000.00')
        interest = self.savings_account.calculate_interest(principal)
        expected = Decimal('4.17')
        self.assertEqual(interest, expected)
    
    def test_calculate_interest_with_3_5_percent_quarterly(self):
        principal = Decimal('1000.00')
        interest = self.current_account.calculate_interest(principal)
        expected = Decimal('8.75')
        self.assertEqual(interest, expected)
    
    def test_calculate_interest_with_zero_principal(self):
        interest = self.savings_account.calculate_interest(Decimal('0'))
        self.assertEqual(interest, Decimal('0'))
    
    def test_calculate_interest_rounding(self):
        principal = Decimal('333.33')
        interest = self.savings_account.calculate_interest(principal)
        self.assertEqual(interest, round(interest, 2))


class TestUserBankAccountModel(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='account@example.com',
            password='testpass123'
        )
        self.account_type = BankAccountType.objects.create(
            name='Test Account',
            maximum_withdrawal_amount=5000,
            annual_interest_rate=6,
            interest_calculation_per_year=4
        )
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender='M',
            birth_date=date(1990, 1, 1),
            balance=Decimal('500.00'),
            interest_start_date=date(2024, 3, 1)
        )
    
    def test_account_creation(self):
        self.assertEqual(self.account.account_no, 1000000001)
        self.assertEqual(self.account.gender, 'M')
        self.assertEqual(self.account.balance, Decimal('500.00'))
    
    def test_account_string_representation(self):
        self.assertEqual(str(self.account), '1000000001')
    
    def test_account_user_relationship(self):
        self.assertEqual(self.account.user, self.user)
        self.assertEqual(self.user.account, self.account)
    
    def test_get_interest_calculation_months_quarterly(self):
        months = self.account.get_interest_calculation_months()
        expected = [3, 6, 9, 12]
        self.assertEqual(months, expected)
    
    def test_get_interest_calculation_months_monthly(self):
        account_type_monthly = BankAccountType.objects.create(
            name='Monthly Interest',
            maximum_withdrawal_amount=5000,
            annual_interest_rate=5,
            interest_calculation_per_year=12
        )
        account = UserBankAccount.objects.create(
            user=User.objects.create_user(email='monthly@example.com', password='pass'),
            account_type=account_type_monthly,
            account_no=1000000002,
            gender='F',
            balance=Decimal('1000.00'),
            interest_start_date=date(2024, 1, 1)
        )
        months = account.get_interest_calculation_months()
        expected = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
        self.assertEqual(months, expected)


class TestUserAddressModel(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='address@example.com',
            password='testpass123'
        )
        self.address = UserAddress.objects.create(
            user=self.user,
            street_address='123 Main St',
            city='São Paulo',
            postal_code=12345678,
            country='Brazil'
        )
    
    def test_address_creation(self):
        self.assertEqual(self.address.street_address, '123 Main St')
        self.assertEqual(self.address.city, 'São Paulo')
        self.assertEqual(self.address.postal_code, 12345678)
        self.assertEqual(self.address.country, 'Brazil')
    
    def test_address_string_representation(self):
        self.assertEqual(str(self.address), 'address@example.com')
    
    def test_address_user_relationship(self):
        self.assertEqual(self.address.user, self.user)
        self.assertEqual(self.user.address, self.address)


class TestUserRegistrationForm(TestCase):
    
    def setUp(self):
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=5000,
            annual_interest_rate=5,
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
            'gender': 'M',
            'birth_date': '1990-01-01'
        }
        form = UserRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_form_creates_user_and_account(self):
        form_data = {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'email': 'jane@example.com',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
            'account_type': self.account_type.id,
            'gender': 'F',
            'birth_date': '1995-05-15'
        }
        form = UserRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())
        user = form.save()
        
        self.assertEqual(user.email, 'jane@example.com')
        self.assertEqual(user.first_name, 'Jane')
        self.assertTrue(user.check_password('SecurePass123!'))
        
        self.assertTrue(hasattr(user, 'account'))
        self.assertEqual(user.account.gender, 'F')
        self.assertEqual(user.account.account_type, self.account_type)
        self.assertEqual(
            user.account.account_no,
            user.id + settings.ACCOUNT_NUMBER_START_FROM
        )
    
    def test_form_password_mismatch(self):
        form_data = {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'password1': 'SecurePass123!',
            'password2': 'DifferentPass456!',
            'account_type': self.account_type.id,
            'gender': 'M',
            'birth_date': '1990-01-01'
        }
        form = UserRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())


class TestUserAddressForm(TestCase):
    
    def test_valid_address_form(self):
        form_data = {
            'street_address': '456 Oak Avenue',
            'city': 'Rio de Janeiro',
            'postal_code': 20040020,
            'country': 'Brazil'
        }
        form = UserAddressForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_form_missing_required_field(self):
        form_data = {
            'street_address': '456 Oak Avenue',
            'city': 'Rio de Janeiro',
            'country': 'Brazil'
        }
        form = UserAddressForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('postal_code', form.errors)
