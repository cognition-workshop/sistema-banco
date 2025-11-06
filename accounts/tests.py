from datetime import date, timedelta
from django.test import TestCase

from accounts.forms import UserRegistrationForm, UserAddressForm
from accounts.models import BankAccountType


class RegistrationFormValidationTests(TestCase):
    
    def setUp(self):
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=5000,
            annual_interest_rate=5.0,
            interest_calculation_per_year=12
        )
    
    def test_birth_date_in_future(self):
        future_date = date.today() + timedelta(days=1)
        form = UserRegistrationForm(data={
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'password1': 'testpass123!',
            'password2': 'testpass123!',
            'account_type': self.account_type.id,
            'gender': 'M',
            'birth_date': future_date
        })
        self.assertFalse(form.is_valid())
        self.assertIn('birth_date', form.errors)
    
    def test_birth_date_under_18(self):
        recent_date = date.today() - timedelta(days=365*10)
        form = UserRegistrationForm(data={
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'password1': 'testpass123!',
            'password2': 'testpass123!',
            'account_type': self.account_type.id,
            'gender': 'M',
            'birth_date': recent_date
        })
        self.assertFalse(form.is_valid())
        self.assertIn('birth_date', form.errors)
    
    def test_birth_date_valid(self):
        valid_date = date.today() - timedelta(days=365*25)
        form = UserRegistrationForm(data={
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'password1': 'testpass123!',
            'password2': 'testpass123!',
            'account_type': self.account_type.id,
            'gender': 'M',
            'birth_date': valid_date
        })
        self.assertTrue(form.is_valid())


class AddressFormValidationTests(TestCase):
    
    def test_short_street_address(self):
        form = UserAddressForm(data={
            'street_address': 'Rua',
            'city': 'São Paulo',
            'postal_code': 12345678,
            'country': 'Brasil'
        })
        self.assertFalse(form.is_valid())
        self.assertIn('street_address', form.errors)
    
    def test_valid_address(self):
        form = UserAddressForm(data={
            'street_address': 'Rua das Flores, 123',
            'city': 'São Paulo',
            'postal_code': 12345678,
            'country': 'Brasil'
        })
        self.assertTrue(form.is_valid())
