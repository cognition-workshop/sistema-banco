from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from accounts.models import BankAccountType, UserBankAccount
from transactions.models import Transaction
from transactions.constants import DEPOSIT, WITHDRAWAL

User = get_user_model()


class TestBankingIntegration(TestCase):
    """Testes de integração do sistema bancário"""

    def setUp(self):
        self.client = Client()
        self.account_type = BankAccountType.objects.create(
            name="Conta Corrente",
            maximum_withdrawal_amount=Decimal("5000.00"),
            annual_interest_rate=Decimal("2.50"),
            interest_calculation_per_year=12,
        )
        self.user = User.objects.create_user(
            email="demo@example.com", password="testpass123"
        )
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1234567890,
            gender="M",
            balance=Decimal("0.00"),
        )

    def test_complete_banking_flow(self):
        """Testa fluxo completo: depósito -> saque -> transações"""
        self.client.post(
            "/transactions/deposit/", {"amount": "1000.00", "transaction_type": DEPOSIT}
        )
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal("1000.00"))

        self.client.post(
            "/transactions/withdraw/",
            {"amount": "300.00", "transaction_type": WITHDRAWAL},
        )
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal("700.00"))

        transactions = Transaction.objects.filter(account=self.account)
        self.assertEqual(transactions.count(), 2)

        response = self.client.get("/transactions/report/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "1000")
        self.assertContains(response, "300")
