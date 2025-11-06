from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from accounts.models import BankAccountType, UserBankAccount
from transactions.models import Transaction
from transactions.constants import DEPOSIT

User = get_user_model()


class TransactionModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="test@example.com", password="testpass123")
        self.account_type = BankAccountType.objects.create(
            name="Savings",
            maximum_withdrawal_amount=10000.00,
            annual_interest_rate=5.0,
            interest_calculation_per_year=12,
        )
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender="M",
            balance=1000.00,
        )

    def test_transaction_creation(self):
        transaction = Transaction.objects.create(
            account=self.account,
            amount=Decimal("100.00"),
            balance_after_transaction=Decimal("1100.00"),
            transaction_type=DEPOSIT,
        )
        self.assertEqual(transaction.amount, Decimal("100.00"))
        self.assertEqual(transaction.transaction_type, DEPOSIT)
