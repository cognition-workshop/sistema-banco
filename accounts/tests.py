import pytest
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from datetime import date, timedelta

from accounts.forms import UserRegistrationForm
from accounts.models import BankAccountType

User = get_user_model()


@pytest.mark.django_db
class TestUserRegistrationValidation(TestCase):
    """Test user registration form validations."""

    def setUp(self):
        self.account_type = BankAccountType.objects.create(
            name="Savings",
            maximum_withdrawal_amount=1000,
            annual_interest_rate=5,
            interest_calculation_per_year=12,
        )

    def test_underage_user_registration_fails(self):
        """Test that users under 18 cannot register."""
        form_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "password1": "SecurePass123!",
            "password2": "SecurePass123!",
            "account_type": self.account_type.id,
            "gender": "M",
            "birth_date": date.today() - timedelta(days=365 * 17),
        }
        form = UserRegistrationForm(data=form_data)

        self.assertFalse(form.is_valid())
        self.assertIn("birth_date", form.errors)
        self.assertIn("18 anos", str(form.errors["birth_date"]))

    def test_valid_user_registration(self):
        """Test that valid user data passes validation."""
        form_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "password1": "SecurePass123!",
            "password2": "SecurePass123!",
            "account_type": self.account_type.id,
            "gender": "M",
            "birth_date": date.today() - timedelta(days=365 * 25),
        }
        form = UserRegistrationForm(data=form_data)

        self.assertTrue(form.is_valid())
