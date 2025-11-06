from django.test import TestCase
from django.contrib.auth import get_user_model
from accounts.models import BankAccountType

User = get_user_model()


class UserModelTest(TestCase):
    def test_user_creation(self):
        user = User.objects.create_user(email="test@example.com", password="testpass123")
        self.assertEqual(user.email, "test@example.com")
        self.assertTrue(user.check_password("testpass123"))


class BankAccountTypeTest(TestCase):
    def test_interest_calculation(self):
        account_type = BankAccountType.objects.create(
            name="Savings",
            maximum_withdrawal_amount=10000.00,
            annual_interest_rate=5.0,
            interest_calculation_per_year=12,
        )
        interest = account_type.calculate_interest(1000)
        self.assertGreater(interest, 0)
