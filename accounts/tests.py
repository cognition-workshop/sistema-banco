from django.test import TestCase
from django.contrib.auth import get_user_model
from accounts.forms import UserRegistrationForm, UserAddressForm
from accounts.models import BankAccountType

User = get_user_model()


class UserRegistrationFormTests(TestCase):
    def setUp(self):
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=10000
        )
    
    def test_valid_registration_form(self):
        """Test that valid registration form is accepted"""
        form_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com',
            'password1': 'securepass123',
            'password2': 'securepass123',
            'account_type': self.account_type.id,
            'gender': 'M',
            'birth_date': '1990-01-01'
        }
        form = UserRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_duplicate_email_validation(self):
        """Test that duplicate email is rejected"""
        User.objects.create_user(
            email='existing@example.com',
            first_name='Existing',
            last_name='User',
            password='pass123'
        )
        form_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'existing@example.com',
            'password1': 'securepass123',
            'password2': 'securepass123',
            'account_type': self.account_type.id,
            'gender': 'M',
            'birth_date': '1990-01-01'
        }
        form = UserRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
    
    def test_underage_user_validation(self):
        """Test that users under 18 are rejected"""
        from django.utils import timezone
        recent_date = timezone.now().date().replace(year=timezone.now().year - 10)
        form_data = {
            'first_name': 'Young',
            'last_name': 'User',
            'email': 'young@example.com',
            'password1': 'securepass123',
            'password2': 'securepass123',
            'account_type': self.account_type.id,
            'gender': 'M',
            'birth_date': recent_date
        }
        form = UserRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('birth_date', form.errors)


class UserRegistrationViewTests(TestCase):
    def test_registration_page_accessible(self):
        """Test that registration page loads"""
        response = self.client.get('/accounts/register/')
        self.assertEqual(response.status_code, 200)
    
    def test_login_page_accessible(self):
        """Test that login page loads"""
        response = self.client.get('/accounts/login/')
        self.assertEqual(response.status_code, 200)
