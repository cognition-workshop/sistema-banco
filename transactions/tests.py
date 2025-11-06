import pytest
from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

from accounts.models import BankAccountType, UserBankAccount
from transactions.models import Transaction
from transactions.constants import DEPOSIT, WITHDRAWAL

User = get_user_model()


@pytest.mark.django_db
class TransactionTestCase(TestCase):
    """Testes para o sistema de transações."""

    def setUp(self):
        """Configuração inicial para cada teste."""
        self.client = Client()

        self.account_type = BankAccountType.objects.create(
            name="Conta Corrente",
            maximum_withdrawal_amount=Decimal("5000.00"),
            annual_interest_rate=Decimal("2.5"),
            interest_calculation_per_year=12,
        )

        self.user = User.objects.create_user(
            email="test@example.com", password="testpass123", first_name="Test", last_name="User"
        )

        self.account = UserBankAccount.objects.create(
            user=self.user, account_type=self.account_type, account_no=1000000001, gender="M", balance=Decimal("1000.00")
        )

    def test_deposit_success(self):
        """Teste de depósito bem-sucedido."""
        initial_balance = self.account.balance
        deposit_amount = Decimal("500.00")

        response = self.client.post(
            reverse("transactions:deposit_money"), {"amount": deposit_amount, "transaction_type": DEPOSIT}
        )

        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, initial_balance + deposit_amount)

    def test_withdraw_success(self):
        """Teste de saque bem-sucedido."""
        initial_balance = self.account.balance
        withdraw_amount = Decimal("200.00")

        response = self.client.post(
            reverse("transactions:withdraw_money"), {"amount": withdraw_amount, "transaction_type": WITHDRAWAL}
        )

        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, initial_balance - withdraw_amount)

    def test_withdraw_insufficient_balance(self):
        """Teste de saque com saldo insuficiente (BUG FIX VALIDATION)."""
        self.account.balance = Decimal("100.00")
        self.account.save()

        withdraw_amount = Decimal("500.00")

        response = self.client.post(
            reverse("transactions:withdraw_money"), {"amount": withdraw_amount, "transaction_type": WITHDRAWAL}
        )

        self.assertContains(response, "Saldo insuficiente", status_code=200)

        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal("100.00"))

    def test_withdraw_below_minimum(self):
        """Teste de saque abaixo do valor mínimo."""
        withdraw_amount = Decimal("5.00")

        response = self.client.post(
            reverse("transactions:withdraw_money"), {"amount": withdraw_amount, "transaction_type": WITHDRAWAL}
        )

        self.assertContains(response, "no mínimo", status_code=200)

    def test_withdraw_above_maximum(self):
        """Teste de saque acima do valor máximo."""
        self.account.balance = Decimal("10000.00")
        self.account.save()

        withdraw_amount = Decimal("6000.00")

        response = self.client.post(
            reverse("transactions:withdraw_money"), {"amount": withdraw_amount, "transaction_type": WITHDRAWAL}
        )

        self.assertContains(response, "no máximo", status_code=200)

    def test_transaction_logging(self):
        """Teste se transações são registradas corretamente."""
        deposit_amount = Decimal("300.00")

        initial_count = Transaction.objects.count()

        self.client.post(reverse("transactions:deposit_money"), {"amount": deposit_amount, "transaction_type": DEPOSIT})

        final_count = Transaction.objects.count()
        self.assertEqual(final_count, initial_count + 1)

        transaction = Transaction.objects.latest("timestamp")
        self.assertEqual(transaction.amount, deposit_amount)
        self.assertEqual(transaction.transaction_type, DEPOSIT)
