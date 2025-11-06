from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from datetime import date

from .models import BankAccountType, UserBankAccount, UserAddress
from .forms import UserAddressForm, UserRegistrationForm
from .constants import MALE, FEMALE


User = get_user_model()


class UserModelTestCase(TestCase):
    
    def setUp(self):
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('5.00'),
            interest_calculation_per_year=12
        )
        
    def test_user_creation_with_email(self):
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('testpass123'))
        self.assertEqual(user.first_name, 'Test')
        
    def test_balance_property_with_account(self):
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        account = UserBankAccount.objects.create(
            user=user,
            account_type=self.account_type,
            account_no=1000000001,
            gender=MALE,
            balance=Decimal('500.00')
        )
        self.assertEqual(user.balance, Decimal('500.00'))
        
    def test_balance_property_without_account(self):
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.assertEqual(user.balance, 0)
        
    def test_user_string_representation(self):
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.assertEqual(str(user), 'test@example.com')


class BankAccountTypeModelTestCase(TestCase):
    
    def setUp(self):
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('5.00'),
            interest_calculation_per_year=12
        )
        
    def test_interest_calculation_basic(self):
        principal = Decimal('1000.00')
        interest = self.account_type.calculate_interest(principal)
        expected = round((principal * (1 + ((Decimal('5.00')/100) / 12))) - principal, 2)
        self.assertEqual(interest, expected)
        
    def test_interest_calculation_zero_principal(self):
        interest = self.account_type.calculate_interest(Decimal('0.00'))
        self.assertEqual(interest, Decimal('0.00'))
        
    def test_interest_calculation_different_rates(self):
        high_rate_account = BankAccountType.objects.create(
            name='Premium',
            maximum_withdrawal_amount=Decimal('10000.00'),
            annual_interest_rate=Decimal('10.00'),
            interest_calculation_per_year=12
        )
        principal = Decimal('1000.00')
        interest = high_rate_account.calculate_interest(principal)
        self.assertGreater(interest, self.account_type.calculate_interest(principal))
        
    def test_string_representation(self):
        self.assertEqual(str(self.account_type), 'Savings')


class UserBankAccountModelTestCase(TestCase):
    
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
        
    def test_account_creation(self):
        account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender=MALE,
            balance=Decimal('100.00')
        )
        self.assertEqual(account.user, self.user)
        self.assertEqual(account.account_type, self.account_type)
        self.assertEqual(account.balance, Decimal('100.00'))
        
    def test_get_interest_calculation_months_monthly(self):
        account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender=MALE,
            interest_start_date=date(2023, 1, 1)
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
            interest_start_date=date(2023, 1, 1)
        )
        months = account.get_interest_calculation_months()
        self.assertEqual(months, [1, 4, 7, 10])
        
    def test_balance_updates(self):
        account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender=MALE,
            balance=Decimal('100.00')
        )
        account.balance += Decimal('50.00')
        account.save()
        account.refresh_from_db()
        self.assertEqual(account.balance, Decimal('150.00'))
        
    def test_string_representation(self):
        account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender=MALE
        )
        self.assertEqual(str(account), '1000000001')


class UserAddressModelTestCase(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
    def test_address_creation(self):
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
        
    def test_one_to_one_relationship(self):
        address = UserAddress.objects.create(
            user=self.user,
            street_address='123 Main St',
            city='New York',
            postal_code=10001,
            country='USA'
        )
        self.assertEqual(self.user.address, address)
        
    def test_string_representation(self):
        address = UserAddress.objects.create(
            user=self.user,
            street_address='123 Main St',
            city='New York',
            postal_code=10001,
            country='USA'
        )
        self.assertEqual(str(address), 'test@example.com')


class UserAddressFormTestCase(TestCase):
    
    def test_valid_form(self):
        form_data = {
            'street_address': '123 Main St',
            'city': 'New York',
            'postal_code': 10001,
            'country': 'USA'
        }
        form = UserAddressForm(data=form_data)
        self.assertTrue(form.is_valid())
        
    def test_required_fields(self):
        form = UserAddressForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('street_address', form.errors)
        self.assertIn('city', form.errors)
        self.assertIn('postal_code', form.errors)
        self.assertIn('country', form.errors)
        
    def test_form_widget_attributes(self):
        form = UserAddressForm()
        for field_name in form.fields:
            widget_attrs = form.fields[field_name].widget.attrs
            self.assertIn('class', widget_attrs)


class UserRegistrationFormTestCase(TestCase):
    
    def setUp(self):
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('5.00'),
            interest_calculation_per_year=12
        )
        
    def test_valid_registration(self):
        form_data = {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'password1': 'testpass123!',
            'password2': 'testpass123!',
            'account_type': self.account_type.id,
            'gender': MALE,
            'birth_date': '1990-01-01'
        }
        form = UserRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())
        
    def test_password_mismatch(self):
        form_data = {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'password1': 'testpass123!',
            'password2': 'differentpass123!',
            'account_type': self.account_type.id,
            'gender': MALE,
            'birth_date': '1990-01-01'
        }
        form = UserRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)
        
    def test_atomic_transaction_creates_user_and_account(self):
        form_data = {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'password1': 'testpass123!',
            'password2': 'testpass123!',
            'account_type': self.account_type.id,
            'gender': MALE,
            'birth_date': '1990-01-01'
        }
        form = UserRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())
        user = form.save()
        
        self.assertTrue(User.objects.filter(email='test@example.com').exists())
        self.assertTrue(hasattr(user, 'account'))
        self.assertEqual(user.account.account_type, self.account_type)
        
    def test_account_number_generation(self):
        form_data = {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'password1': 'testpass123!',
            'password2': 'testpass123!',
            'account_type': self.account_type.id,
            'gender': MALE,
            'birth_date': '1990-01-01'
        }
        form = UserRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())
        user = form.save()
        
        expected_account_no = user.id + 1000000000
        self.assertEqual(user.account.account_no, expected_account_no)


class UserRegistrationViewTestCase(TestCase):
    
    def setUp(self):
        self.client = Client()
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('5.00'),
            interest_calculation_per_year=12
        )
        
    def test_get_request_returns_forms(self):
        response = self.client.get(reverse('accounts:user_registration'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('registration_form', response.context)
        self.assertIn('address_form', response.context)
        
    def test_post_with_valid_data_creates_user_and_account(self):
        form_data = {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'password1': 'testpass123!',
            'password2': 'testpass123!',
            'account_type': self.account_type.id,
            'gender': MALE,
            'birth_date': '1990-01-01',
            'street_address': '123 Main St',
            'city': 'New York',
            'postal_code': 10001,
            'country': 'USA'
        }
        response = self.client.post(reverse('accounts:user_registration'), data=form_data)
        
        self.assertEqual(User.objects.count(), 1)
        user = User.objects.first()
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(hasattr(user, 'account'))
        self.assertTrue(hasattr(user, 'address'))
        
    def test_authenticated_user_redirect(self):
        user = User.objects.create_user(
            email='existing@example.com',
            password='testpass123'
        )
        self.client.login(email='existing@example.com', password='testpass123')
        response = self.client.get(reverse('accounts:user_registration'))
        self.assertEqual(response.status_code, 302)


class AuthViewsTestCase(TestCase):
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
    def test_login_view_get(self):
        response = self.client.get(reverse('accounts:user_login'))
        self.assertEqual(response.status_code, 200)
        
    def test_logout_view(self):
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(reverse('accounts:user_logout'))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(response.wsgi_request.user.is_authenticated)
