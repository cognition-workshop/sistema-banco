from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.conf import settings
from datetime import date

from accounts.models import User, BankAccountType, UserBankAccount, UserAddress
from accounts.forms import UserRegistrationForm, UserAddressForm
from accounts.constants import MALE, FEMALE


class UserModelTest(TestCase):

    def test_create_user_with_email(self):
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('testpass123'))
        self.assertEqual(user.first_name, 'Test')
        self.assertEqual(user.last_name, 'User')

    def test_user_string_representation(self):
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.assertEqual(str(user), 'test@example.com')

    def test_user_balance_property_with_account(self):
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('5.00'),
            interest_calculation_per_year=12
        )
        account = UserBankAccount.objects.create(
            user=user,
            account_type=account_type,
            account_no=1000000001,
            gender=MALE,
            birth_date=date(1990, 1, 1),
            balance=Decimal('1000.00')
        )
        self.assertEqual(user.balance, Decimal('1000.00'))

    def test_user_balance_property_without_account(self):
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.assertEqual(user.balance, 0)


class BankAccountTypeModelTest(TestCase):

    def test_create_bank_account_type(self):
        account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('5.00'),
            interest_calculation_per_year=12
        )
        self.assertEqual(account_type.name, 'Savings')
        self.assertEqual(account_type.maximum_withdrawal_amount, Decimal('5000.00'))
        self.assertEqual(account_type.annual_interest_rate, Decimal('5.00'))
        self.assertEqual(account_type.interest_calculation_per_year, 12)

    def test_calculate_interest_monthly(self):
        account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('5.00'),
            interest_calculation_per_year=12
        )
        interest = account_type.calculate_interest(Decimal('1000.00'))
        expected_interest = (Decimal('1000.00') * (1 + ((Decimal('5.00')/100) / 12))) - Decimal('1000.00')
        self.assertEqual(interest, round(expected_interest, 2))

    def test_calculate_interest_quarterly(self):
        account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('6.00'),
            interest_calculation_per_year=4
        )
        interest = account_type.calculate_interest(Decimal('2000.00'))
        expected_interest = (Decimal('2000.00') * (1 + ((Decimal('6.00')/100) / 4))) - Decimal('2000.00')
        self.assertEqual(interest, round(expected_interest, 2))

    def test_bank_account_type_string_representation(self):
        account_type = BankAccountType.objects.create(
            name='Current',
            maximum_withdrawal_amount=Decimal('10000.00'),
            annual_interest_rate=Decimal('3.00'),
            interest_calculation_per_year=12
        )
        self.assertEqual(str(account_type), 'Current')


class UserBankAccountModelTest(TestCase):

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

    def test_create_user_bank_account(self):
        account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender=MALE,
            birth_date=date(1990, 1, 1),
            balance=Decimal('1000.00')
        )
        self.assertEqual(account.user, self.user)
        self.assertEqual(account.account_type, self.account_type)
        self.assertEqual(account.account_no, 1000000001)
        self.assertEqual(account.gender, MALE)
        self.assertEqual(account.balance, Decimal('1000.00'))

    def test_account_number_generation(self):
        expected_account_no = self.user.id + settings.ACCOUNT_NUMBER_START_FROM
        account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=expected_account_no,
            gender=MALE,
            birth_date=date(1990, 1, 1)
        )
        self.assertEqual(account.account_no, expected_account_no)

    def test_get_interest_calculation_months_monthly(self):
        account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender=MALE,
            birth_date=date(1990, 1, 1),
            interest_start_date=date(2024, 1, 1)
        )
        months = account.get_interest_calculation_months()
        self.assertEqual(months, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])

    def test_get_interest_calculation_months_quarterly(self):
        quarterly_account_type = BankAccountType.objects.create(
            name='Quarterly',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('5.00'),
            interest_calculation_per_year=4
        )
        account = UserBankAccount.objects.create(
            user=self.user,
            account_type=quarterly_account_type,
            account_no=1000000002,
            gender=MALE,
            birth_date=date(1990, 1, 1),
            interest_start_date=date(2024, 2, 1)
        )
        months = account.get_interest_calculation_months()
        self.assertEqual(months, [2, 5, 8, 11])

    def test_user_bank_account_string_representation(self):
        account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender=MALE,
            birth_date=date(1990, 1, 1)
        )
        self.assertEqual(str(account), '1000000001')


class UserAddressModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )

    def test_create_user_address(self):
        address = UserAddress.objects.create(
            user=self.user,
            street_address='123 Main St',
            city='New York',
            postal_code=10001,
            country='USA'
        )
        self.assertEqual(address.user, self.user)
        self.assertEqual(address.street_address, '123 Main St')
        self.assertEqual(address.city, 'New York')
        self.assertEqual(address.postal_code, 10001)
        self.assertEqual(address.country, 'USA')

    def test_user_address_string_representation(self):
        address = UserAddress.objects.create(
            user=self.user,
            street_address='456 Oak Ave',
            city='Boston',
            postal_code=20001,
            country='USA'
        )
        self.assertEqual(str(address), 'test@example.com')


class UserRegistrationFormTest(TestCase):

    def setUp(self):
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('5.00'),
            interest_calculation_per_year=12
        )

    def test_valid_registration_form(self):
        form_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com',
            'password1': 'securepass123',
            'password2': 'securepass123',
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
            'email': 'jane.smith@example.com',
            'password1': 'securepass123',
            'password2': 'securepass123',
            'account_type': self.account_type.id,
            'gender': FEMALE,
            'birth_date': '1992-05-15'
        }
        form = UserRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        user = form.save()
        self.assertIsNotNone(user)
        self.assertEqual(user.email, 'jane.smith@example.com')
        self.assertTrue(hasattr(user, 'account'))
        self.assertEqual(user.account.gender, FEMALE)
        self.assertEqual(user.account.account_type, self.account_type)

    def test_registration_form_password_mismatch(self):
        form_data = {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'password1': 'password123',
            'password2': 'differentpassword',
            'account_type': self.account_type.id,
            'gender': MALE,
            'birth_date': '1990-01-01'
        }
        form = UserRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())


class UserAddressFormTest(TestCase):

    def test_valid_address_form(self):
        form_data = {
            'street_address': '789 Elm St',
            'city': 'Chicago',
            'postal_code': 60601,
            'country': 'USA'
        }
        form = UserAddressForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_address_form_missing_field(self):
        form_data = {
            'street_address': '789 Elm St',
            'city': 'Chicago',
            'country': 'USA'
        }
        form = UserAddressForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('postal_code', form.errors)


class UserRegistrationViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('5.00'),
            interest_calculation_per_year=12
        )

    def test_registration_view_creates_user_and_account(self):
        response = self.client.post(reverse('accounts:user_registration'), {
            'first_name': 'Alice',
            'last_name': 'Johnson',
            'email': 'alice.johnson@example.com',
            'password1': 'securepass123',
            'password2': 'securepass123',
            'account_type': self.account_type.id,
            'gender': FEMALE,
            'birth_date': '1995-03-20',
            'street_address': '101 Park Ave',
            'city': 'Seattle',
            'postal_code': 98101,
            'country': 'USA'
        })
        
        user = User.objects.filter(email='alice.johnson@example.com').first()
        self.assertIsNotNone(user)
        self.assertTrue(hasattr(user, 'account'))
        self.assertTrue(hasattr(user, 'address'))
        self.assertEqual(user.address.city, 'Seattle')

    def test_registration_view_redirects_authenticated_user(self):
        user = User.objects.create_user(
            email='existing@example.com',
            password='testpass123'
        )
        self.client.login(email='existing@example.com', password='testpass123')
        
        response = self.client.get(reverse('accounts:user_registration'))
        self.assertEqual(response.status_code, 302)
