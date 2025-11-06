from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model

from accounts.models import UserBankAccount, BankAccountType
from transactions.models import Transaction
from transactions.constants import DEPOSIT, WITHDRAWAL
from transactions.forms import DepositForm, WithdrawForm

User = get_user_model()


class TransactionAtomicityTests(TestCase):
    """Test that all balance operations are atomic."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
        )

        self.account_type = BankAccountType.objects.create(
            name="Savings",
            maximum_withdrawal_amount=Decimal("5000.00"),
            annual_interest_rate=Decimal("5.00"),
            interest_calculation_per_year=12,
        )

        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender="M",
            balance=Decimal("1000.00"),
        )

    def test_deposit_is_atomic(self):
        """Test that deposits are atomic transactions."""
        initial_balance = self.account.balance

        form = DepositForm(
            data={"amount": Decimal("100.00")},
            initial={"transaction_type": DEPOSIT},
            account=self.account,
        )

        if not form.is_valid():
            self.fail(f"Form validation failed: {form.errors}")

        form.save()

        self.account.refresh_from_db()

        self.assertEqual(self.account.balance, initial_balance + Decimal("100.00"))

        self.assertEqual(Transaction.objects.count(), 1)

    def test_withdraw_validates_balance(self):
        """Test that withdrawals validate sufficient balance."""
        form = WithdrawForm(
            data={"amount": Decimal("2000.00")},
            initial={"transaction_type": WITHDRAWAL},
            account=self.account,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("amount", form.errors)

    def test_withdraw_is_atomic(self):
        """Test that withdrawals are atomic transactions."""
        initial_balance = self.account.balance

        form = WithdrawForm(
            data={"amount": Decimal("100.00")},
            initial={"transaction_type": WITHDRAWAL},
            account=self.account,
        )

        if not form.is_valid():
            self.fail(f"Form validation failed: {form.errors}")

        form.save()

        self.account.refresh_from_db()

        self.assertEqual(self.account.balance, initial_balance - Decimal("100.00"))


class ValidationTests(TestCase):
    """Test validation logic."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email="test@example.com", password="testpass123"
        )

        self.account_type = BankAccountType.objects.create(
            name="Savings",
            maximum_withdrawal_amount=Decimal("5000.00"),
            annual_interest_rate=Decimal("5.00"),
            interest_calculation_per_year=12,
        )

        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender="M",
            balance=Decimal("1000.00"),
        )

    def test_negative_amount_rejected(self):
        """Test that negative amounts are rejected."""
        form = DepositForm(
            data={"amount": Decimal("-100.00")},
            initial={"transaction_type": DEPOSIT},
            account=self.account,
        )

        self.assertFalse(form.is_valid())
