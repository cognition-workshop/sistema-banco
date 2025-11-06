import pytest
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.conf import settings

from accounts.models import UserBankAccount, BankAccountType
from transactions.models import Transaction
from transactions.constants import DEPOSIT, WITHDRAWAL

User = get_user_model()


@pytest.mark.django_db
class TestWithdrawalValidation(TestCase):
    """Test the withdrawal balance validation bug fix."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
        )

        self.account_type = BankAccountType.objects.create(
            name="Savings",
            maximum_withdrawal_amount=Decimal("1000.00"),
            annual_interest_rate=Decimal("5.00"),
            interest_calculation_per_year=12,
        )

        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender="M",
            balance=Decimal("100.00"),
        )

    def test_withdrawal_exceeds_balance(self):
        """Test that withdrawal fails when amount exceeds balance."""
        from transactions.forms import WithdrawForm

        form_data = {"amount": Decimal("150.00")}
        form = WithdrawForm(
            data=form_data,
            initial={"transaction_type": WITHDRAWAL},
            account=self.account,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("amount", form.errors)
        self.assertIn("Saldo insuficiente", str(form.errors["amount"]))

    def test_withdrawal_within_balance(self):
        """Test that withdrawal succeeds when amount is within balance."""
        from transactions.forms import WithdrawForm

        form_data = {"amount": Decimal("50.00")}
        form = WithdrawForm(
            data=form_data,
            initial={"transaction_type": WITHDRAWAL},
            account=self.account,
        )

        self.assertTrue(form.is_valid())


@pytest.mark.django_db
class TestHealthCheckEndpoints(TestCase):
    """Test health check endpoints."""

    def setUp(self):
        self.client = Client()

    def test_health_check_basic(self):
        """Test basic health check endpoint."""
        response = self.client.get(reverse("health"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "healthy")

    def test_health_check_database(self):
        """Test database health check endpoint."""
        response = self.client.get(reverse("health_db"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "healthy")
