from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.conf import settings

from .models import BankAccountType, UserBankAccount, UserAddress
from .forms import UserRegistrationForm, UserAddressForm
from .constants import MALE, FEMALE


User = get_user_model()


class UserModelTest(TestCase):
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

    def test_user_creation_with_email(self):
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertEqual(str(self.user), 'test@example.com')
        self.assertTrue(self.user.check_password('testpass123'))

    def test_user_balance_property_without_account(self):
        self.assertEqual(self.user.balance, 0)

    def test_user_balance_property_with_account(self):
        UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender=MALE,
            birth_date=date(1990, 1, 1),
            balance=Decimal('1000.00')
        )
        self.assertEqual(self.user.balance, Decimal('1000.00'))


class BankAccountTypeModelTest(TestCase):
    def setUp(self):
        self.savings_account = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('5.00'),
            interest_calculation_per_year=12
        )
        self.current_account = BankAccountType.objects.create(
            name='Current',
            maximum_withdrawal_amount=Decimal('10000.00'),
            annual_interest_rate=Decimal('3.50'),
            interest_calculation_per_year=4
        )

    def test_bank_account_type_creation(self):
        self.assertEqual(self.savings_account.name, 'Savings')
        self.assertEqual(str(self.savings_account), 'Savings')

    def test_calculate_interest_monthly(self):
        principal = Decimal('1000.00')
        interest = self.savings_account.calculate_interest(principal)
        expected = round((principal * (1 + ((Decimal('5.00')/100) / 12))) - principal, 2)
        self.assertEqual(interest, expected)

    def test_calculate_interest_quarterly(self):
        principal = Decimal('2000.00')
        interest = self.current_account.calculate_interest(principal)
        expected = round((principal * (1 + ((Decimal('3.50')/100) / 4))) - principal, 2)
        self.assertEqual(interest, expected)

    def test_calculate_interest_zero_principal(self):
        interest = self.savings_account.calculate_interest(Decimal('0.00'))
        self.assertEqual(interest, Decimal('0.00'))

    def test_calculate_interest_large_amount(self):
        principal = Decimal('1000000.00')
        interest = self.savings_account.calculate_interest(principal)
        self.assertGreater(interest, Decimal('0.00'))


class UserBankAccountModelTest(TestCase):
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
            account_no=settings.ACCOUNT_NUMBER_START_FROM + self.user.id,
            gender=MALE,
            birth_date=date(1990, 1, 1),
            balance=Decimal('1000.00'),
            interest_start_date=date(2024, 1, 1)
        )

    def test_account_number_generation(self):
        expected_account_no = settings.ACCOUNT_NUMBER_START_FROM + self.user.id
        self.assertEqual(self.bank_account.account_no, expected_account_no)

    def test_str_representation(self):
        self.assertEqual(str(self.bank_account), str(self.bank_account.account_no))

    def test_get_interest_calculation_months_monthly(self):
        months = self.bank_account.get_interest_calculation_months()
        expected = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
        self.assertEqual(months, expected)

    def test_get_interest_calculation_months_quarterly(self):
        quarterly_account_type = BankAccountType.objects.create(
            name='Current',
            maximum_withdrawal_amount=Decimal('10000.00'),
            annual_interest_rate=Decimal('3.50'),
            interest_calculation_per_year=4
        )
        user2 = User.objects.create_user(email='user2@example.com', password='pass123')
        account = UserBankAccount.objects.create(
            user=user2,
            account_type=quarterly_account_type,
            account_no=1000000002,
            gender=FEMALE,
            birth_date=date(1995, 6, 15),
            interest_start_date=date(2024, 3, 1)
        )
        months = account.get_interest_calculation_months()
        expected = [3, 6, 9, 12]
        self.assertEqual(months, expected)

    def test_get_interest_calculation_months_bimonthly(self):
        bimonthly_account_type = BankAccountType.objects.create(
            name='Premium',
            maximum_withdrawal_amount=Decimal('20000.00'),
            annual_interest_rate=Decimal('6.00'),
            interest_calculation_per_year=6
        )
        user3 = User.objects.create_user(email='user3@example.com', password='pass123')
        account = UserBankAccount.objects.create(
            user=user3,
            account_type=bimonthly_account_type,
            account_no=1000000003,
            gender=MALE,
            birth_date=date(1988, 2, 20),
            interest_start_date=date(2024, 2, 1)
        )
        months = account.get_interest_calculation_months()
        expected = [2, 4, 6, 8, 10, 12]
        self.assertEqual(months, expected)


class UserAddressModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.address = UserAddress.objects.create(
            user=self.user,
            street_address='123 Main St',
            city='Test City',
            postal_code=12345,
            country='Test Country'
        )

    def test_address_creation(self):
        self.assertEqual(self.address.street_address, '123 Main St')
        self.assertEqual(self.address.city, 'Test City')
        self.assertEqual(self.address.postal_code, 12345)
        self.assertEqual(self.address.country, 'Test Country')

    def test_str_representation(self):
        self.assertEqual(str(self.address), 'test@example.com')


class UserAddressFormTest(TestCase):
    def test_valid_address_form(self):
        form_data = {
            'street_address': '456 Elm St',
            'city': 'Another City',
            'postal_code': 54321,
            'country': 'Another Country'
        }
        form = UserAddressForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_missing_required_fields(self):
        form_data = {
            'street_address': '456 Elm St',
        }
        form = UserAddressForm(data=form_data)
        self.assertFalse(form.is_valid())


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
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
            'account_type': self.account_type.id,
            'gender': MALE,
            'birth_date': date(1990, 1, 1)
        }
        form = UserRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_password_mismatch(self):
        form_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com',
            'password1': 'SecurePass123!',
            'password2': 'DifferentPass123!',
            'account_type': self.account_type.id,
            'gender': MALE,
            'birth_date': date(1990, 1, 1)
        }
        form = UserRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_form_saves_user_and_account(self):
        form_data = {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'email': 'jane.smith@example.com',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
            'account_type': self.account_type.id,
            'gender': FEMALE,
            'birth_date': date(1995, 6, 15)
        }
        form = UserRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())
        user = form.save()
        
        self.assertIsNotNone(user.id)
        self.assertEqual(user.email, 'jane.smith@example.com')
        self.assertTrue(user.check_password('SecurePass123!'))
        
        self.assertTrue(hasattr(user, 'account'))
        self.assertEqual(user.account.account_no, user.id + settings.ACCOUNT_NUMBER_START_FROM)
        self.assertEqual(user.account.gender, FEMALE)
        self.assertEqual(user.account.birth_date, date(1995, 6, 15))


class UserRegistrationViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('5.00'),
            interest_calculation_per_year=12
        )
        self.registration_url = reverse('accounts:user_registration')

    def test_successful_registration(self):
        form_data = {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'newuser@example.com',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
            'account_type': self.account_type.id,
            'gender': MALE,
            'birth_date': '1990-01-01',
            'street_address': '123 Test St',
            'city': 'Test City',
            'postal_code': 12345,
            'country': 'Test Country'
        }
        response = self.client.post(self.registration_url, form_data)
        
        self.assertEqual(response.status_code, 302)
        
        user = User.objects.get(email='newuser@example.com')
        self.assertIsNotNone(user)
        self.assertTrue(hasattr(user, 'account'))
        self.assertTrue(hasattr(user, 'address'))
        
        expected_account_no = user.id + settings.ACCOUNT_NUMBER_START_FROM
        self.assertEqual(user.account.account_no, expected_account_no)

    def test_authenticated_user_redirect(self):
        user = User.objects.create_user(
            email='existing@example.com',
            password='pass123'
        )
        self.client.login(username='existing@example.com', password='pass123')
        response = self.client.get(self.registration_url)
        self.assertEqual(response.status_code, 302)
