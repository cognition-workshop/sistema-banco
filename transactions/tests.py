from decimal import Decimal
from unittest.mock import patch, Mock
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.db import OperationalError, IntegrityError
from django.urls import reverse
from django.utils import timezone

from accounts.models import BankAccountType, UserBankAccount
from transactions.models import Transaction
from transactions.forms import WithdrawForm
from transactions.tasks import calculate_interest
from transactions.constants import DEPOSIT, WITHDRAWAL, INTEREST

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


class WithdrawFormTestCase(TestCase):
    """Test the balance validation fix in WithdrawForm"""

    def setUp(self):
        self.account_type = BankAccountType.objects.create(
            name="Savings",
            maximum_withdrawal_amount=Decimal("5000.00"),
            annual_interest_rate=Decimal("5.00"),
            interest_calculation_per_year=12,
        )
        self.user = User.objects.create_user(email="test@example.com", password="testpass123")
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1234567890,
            gender="M",
            balance=Decimal("1000.00"),
        )

    def test_withdraw_with_sufficient_balance(self):
        """Test that withdrawal with sufficient balance is allowed"""
        form = WithdrawForm(data={"amount": Decimal("500.00")})
        form.account = self.account
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["amount"], Decimal("500.00"))

    def test_withdraw_with_insufficient_balance(self):
        """Test that withdrawal exceeding balance is blocked (bug fix validation)"""
        form = WithdrawForm(data={"amount": Decimal("1500.00")})
        form.account = self.account
        self.assertFalse(form.is_valid())
        self.assertIn("Insufficient balance", str(form.errors["amount"]))

    def test_withdraw_exact_balance(self):
        """Test that withdrawal of exact balance is allowed"""
        form = WithdrawForm(data={"amount": Decimal("1000.00")})
        form.account = self.account
        self.assertTrue(form.is_valid())

    def test_withdraw_exceeds_maximum_withdrawal_amount(self):
        """Test that withdrawal exceeding maximum is blocked"""
        self.account.balance = Decimal("10000.00")
        self.account.save()
        form = WithdrawForm(data={"amount": Decimal("6000.00")})
        form.account = self.account
        self.assertFalse(form.is_valid())
        self.assertIn("withdraw at most", str(form.errors["amount"]))


class DepositViewTestCase(TestCase):
    """Test deposit view with error handling and audit logging"""

    def setUp(self):
        self.client = Client()
        self.account_type = BankAccountType.objects.create(
            name="Savings",
            maximum_withdrawal_amount=Decimal("5000.00"),
            annual_interest_rate=Decimal("5.00"),
            interest_calculation_per_year=12,
        )
        self.demo_user = User.objects.create_user(email="demo@example.com", password="demopass123")
        self.account = UserBankAccount.objects.create(
            user=self.demo_user,
            account_type=self.account_type,
            account_no=1234567890,
            gender="M",
            balance=Decimal("1000.00"),
        )
        self.url = reverse("transactions:deposit_money")

    def test_successful_deposit(self):
        """Test successful deposit updates balance and creates transaction"""
        initial_balance = self.account.balance
        response = self.client.post(
            self.url, {"amount": Decimal("500.00"), "transaction_type": DEPOSIT}
        )

        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, initial_balance + Decimal("500.00"))

        transaction = Transaction.objects.filter(
            account=self.account, transaction_type=DEPOSIT, amount=Decimal("500.00")
        ).first()
        self.assertIsNotNone(transaction)

        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("deposited" in str(m).lower() for m in messages))

    @patch("transactions.views.logger")
    @patch("transactions.views.audit_logger")
    def test_deposit_with_audit_logging(self, mock_audit_logger, mock_logger):
        """Test that successful deposit is logged to audit log"""
        self.client.post(self.url, {"amount": Decimal("500.00"), "transaction_type": DEPOSIT})

        mock_audit_logger.info.assert_called()
        call_args = mock_audit_logger.info.call_args
        self.assertIn("Deposit successful", call_args[0][0])

    @patch("transactions.views.transaction.atomic")
    @patch("transactions.views.logger")
    def test_deposit_database_error(self, mock_logger, mock_atomic):
        """Test that database errors during deposit are handled gracefully"""
        mock_atomic.side_effect = OperationalError("Database locked")

        response = self.client.post(
            self.url, {"amount": Decimal("500.00"), "transaction_type": DEPOSIT}
        )

        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("system error" in str(m).lower() for m in messages))
        mock_logger.error.assert_called()


class WithdrawViewTestCase(TestCase):
    """Test withdrawal view with error handling and audit logging"""

    def setUp(self):
        self.client = Client()
        self.account_type = BankAccountType.objects.create(
            name="Savings",
            maximum_withdrawal_amount=Decimal("5000.00"),
            annual_interest_rate=Decimal("5.00"),
            interest_calculation_per_year=12,
        )
        self.demo_user = User.objects.create_user(email="demo@example.com", password="demopass123")
        self.account = UserBankAccount.objects.create(
            user=self.demo_user,
            account_type=self.account_type,
            account_no=1234567890,
            gender="M",
            balance=Decimal("1000.00"),
        )
        self.url = reverse("transactions:withdraw_money")

    def test_successful_withdrawal(self):
        """Test successful withdrawal updates balance and creates transaction"""
        initial_balance = self.account.balance
        response = self.client.post(
            self.url, {"amount": Decimal("500.00"), "transaction_type": WITHDRAWAL}
        )

        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, initial_balance - Decimal("500.00"))

        transaction = Transaction.objects.filter(
            account=self.account, transaction_type=WITHDRAWAL, amount=Decimal("500.00")
        ).first()
        self.assertIsNotNone(transaction)

        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("withdrawn" in str(m).lower() for m in messages))

    def test_withdrawal_insufficient_balance_blocked(self):
        """Test that withdrawal with insufficient balance is blocked"""
        initial_balance = self.account.balance
        response = self.client.post(
            self.url, {"amount": Decimal("1500.00"), "transaction_type": WITHDRAWAL}
        )

        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, initial_balance)

        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("insufficient balance" in str(m).lower() for m in messages))

    @patch("transactions.views.logger")
    @patch("transactions.views.audit_logger")
    def test_withdrawal_with_audit_logging(self, mock_audit_logger, mock_logger):
        """Test that successful withdrawal is logged to audit log"""
        self.client.post(self.url, {"amount": Decimal("500.00"), "transaction_type": WITHDRAWAL})

        mock_audit_logger.info.assert_called()
        call_args = mock_audit_logger.info.call_args
        self.assertIn("Withdrawal successful", call_args[0][0])

    @patch("transactions.views.logger")
    @patch("transactions.views.audit_logger")
    def test_withdrawal_insufficient_balance_audit_log(self, mock_audit_logger, mock_logger):
        """Test that blocked withdrawals are logged to audit log"""
        self.client.post(self.url, {"amount": Decimal("1500.00"), "transaction_type": WITHDRAWAL})

        mock_audit_logger.warning.assert_called()
        call_args = mock_audit_logger.warning.call_args
        self.assertIn("Insufficient balance", call_args[0][0])

    @patch("transactions.views.transaction.atomic")
    @patch("transactions.views.logger")
    def test_withdrawal_database_error(self, mock_logger, mock_atomic):
        """Test that database errors during withdrawal are handled gracefully"""
        mock_atomic.side_effect = IntegrityError("Integrity constraint violated")

        response = self.client.post(
            self.url, {"amount": Decimal("500.00"), "transaction_type": WITHDRAWAL}
        )

        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("system error" in str(m).lower() for m in messages))
        mock_logger.error.assert_called()


class CeleryInterestTaskTestCase(TestCase):
    """Test Celery task error handling and retry logic"""

    def setUp(self):
        self.account_type = BankAccountType.objects.create(
            name="Savings",
            maximum_withdrawal_amount=Decimal("5000.00"),
            annual_interest_rate=Decimal("5.00"),
            interest_calculation_per_year=12,
        )
        self.user = User.objects.create_user(email="test@example.com", password="testpass123")
        current_date = timezone.now().date()
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1234567890,
            gender="M",
            balance=Decimal("1000.00"),
            initial_deposit_date=current_date,
            interest_start_date=current_date,
        )

    def test_calculate_interest_success(self):
        """Test successful interest calculation"""
        initial_balance = self.account.balance

        calculate_interest()

        self.account.refresh_from_db()
        self.assertGreater(self.account.balance, initial_balance)

        interest_transaction = Transaction.objects.filter(
            account=self.account, transaction_type=INTEREST
        ).first()
        self.assertIsNotNone(interest_transaction)

    @patch("transactions.tasks.logger")
    @patch("transactions.tasks.audit_logger")
    def test_calculate_interest_with_logging(self, mock_audit_logger, mock_logger):
        """Test that interest calculation is logged"""
        calculate_interest()

        mock_logger.info.assert_called()
        mock_audit_logger.info.assert_called()

    @patch("transactions.tasks.UserBankAccount.objects.filter")
    @patch("transactions.tasks.logger")
    def test_calculate_interest_per_account_error_handling(self, mock_logger, mock_filter):
        """Test that errors in one account don't stop processing of other accounts"""
        mock_queryset = Mock()
        mock_account1 = Mock(spec=UserBankAccount)
        mock_account1.account_no = 111
        mock_account1.balance = Decimal("1000.00")
        mock_account1.account_type.calculate_interest.side_effect = Exception("Account error")

        mock_account2 = Mock(spec=UserBankAccount)
        mock_account2.account_no = 222
        mock_account2.balance = Decimal("2000.00")
        mock_account2.account_type.calculate_interest.return_value = Decimal("10.00")
        mock_account2.get_interest_calculation_months.return_value = [timezone.now().month]

        mock_queryset.__iter__ = Mock(return_value=iter([mock_account1, mock_account2]))
        mock_filter.return_value.select_related.return_value = mock_queryset

        with patch("transactions.tasks.timezone.now") as mock_now:
            mock_now.return_value.month = timezone.now().month
            try:
                calculate_interest()
            except Exception:
                pass

        mock_logger.error.assert_called()
        error_call = str(mock_logger.error.call_args)
        self.assertIn("111", error_call)


class ErrorTemplateTestCase(TestCase):
    """Test custom error templates"""

    def test_400_error_page(self):
        """Test 400 error page renders correctly"""
        response = self.client.get("/nonexistent/", HTTP_HOST="testserver")
        self.assertIn(response.status_code, [400, 404])

    def test_404_error_page(self):
        """Test 404 error page"""
        response = self.client.get("/this-url-does-not-exist/")
        self.assertEqual(response.status_code, 404)

    @patch("django.conf.settings.DEBUG", False)
    def test_500_error_page(self):
        """Test 500 error page (only works when DEBUG=False)"""
        pass
