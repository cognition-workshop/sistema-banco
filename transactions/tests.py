from decimal import Decimal
from datetime import date, datetime, timedelta
from unittest.mock import patch, Mock
from django.test import TestCase, RequestFactory
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.messages.storage.fallback import FallbackStorage

from accounts.models import BankAccountType, UserBankAccount
from accounts.constants import MALE
from transactions.models import Transaction, FailedTransaction
from transactions.forms import DepositForm, WithdrawForm, TransactionDateRangeForm
from transactions.views import DepositMoneyView, WithdrawMoneyView, TransactionRepostView
from transactions.tasks import calculate_interest
from transactions.constants import DEPOSIT, WITHDRAWAL, INTEREST
from banking_system.middleware import IPCaptureMiddleware


User = get_user_model()


class TransactionModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='transaction@example.com',
            password='testpass123'
        )
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=5000,
            annual_interest_rate=5.0,
            interest_calculation_per_year=12
        )
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender=MALE,
            birth_date=date(1990, 1, 1),
            balance=1000.00
        )

    def test_transaction_creation(self):
        transaction = Transaction.objects.create(
            account=self.account,
            amount=100.00,
            balance_after_transaction=1100.00,
            transaction_type=DEPOSIT
        )
        self.assertEqual(transaction.amount, Decimal('100.00'))
        self.assertEqual(transaction.transaction_type, DEPOSIT)
        self.assertEqual(str(transaction), '1000000001')

    def test_transaction_immutability_cannot_update(self):
        transaction = Transaction.objects.create(
            account=self.account,
            amount=100.00,
            balance_after_transaction=1100.00,
            transaction_type=DEPOSIT
        )
        transaction.amount = 200.00
        with self.assertRaises(ValidationError) as context:
            transaction.save()
        self.assertIn('não podem ser modificadas', str(context.exception))

    def test_transaction_cannot_be_deleted(self):
        transaction = Transaction.objects.create(
            account=self.account,
            amount=100.00,
            balance_after_transaction=1100.00,
            transaction_type=DEPOSIT
        )
        with self.assertRaises(ValidationError) as context:
            transaction.delete()
        self.assertIn('não podem ser deletadas', str(context.exception))

    def test_transaction_ordering(self):
        trans1 = Transaction.objects.create(
            account=self.account,
            amount=100.00,
            balance_after_transaction=1100.00,
            transaction_type=DEPOSIT
        )
        trans2 = Transaction.objects.create(
            account=self.account,
            amount=50.00,
            balance_after_transaction=1150.00,
            transaction_type=DEPOSIT
        )
        transactions = Transaction.objects.all()
        self.assertEqual(transactions[0], trans1)
        self.assertEqual(transactions[1], trans2)

    def test_transaction_with_metadata(self):
        transaction = Transaction.objects.create(
            account=self.account,
            amount=100.00,
            balance_after_transaction=1100.00,
            transaction_type=DEPOSIT,
            ip_address='192.168.1.1',
            geolocation='São Paulo, Brazil',
            channel='web',
            hash_signature='abc123def456'
        )
        self.assertEqual(transaction.ip_address, '192.168.1.1')
        self.assertEqual(transaction.geolocation, 'São Paulo, Brazil')
        self.assertEqual(transaction.channel, 'web')


class FailedTransactionModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='failed@example.com',
            password='testpass123'
        )
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=5000,
            annual_interest_rate=5.0,
            interest_calculation_per_year=12
        )
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000002,
            gender=MALE,
            birth_date=date(1990, 1, 1),
            balance=100.00
        )

    def test_failed_transaction_creation(self):
        failed_trans = FailedTransaction.objects.create(
            account=self.account,
            attempted_amount=10000.00,
            attempted_transaction_type=WITHDRAWAL,
            failure_reason='Insufficient funds'
        )
        self.assertEqual(failed_trans.attempted_amount, Decimal('10000.00'))
        self.assertEqual(failed_trans.failure_reason, 'Insufficient funds')

    def test_failed_transaction_str(self):
        failed_trans = FailedTransaction.objects.create(
            account=self.account,
            attempted_amount=10000.00,
            attempted_transaction_type=WITHDRAWAL,
            failure_reason='Insufficient funds'
        )
        self.assertIn('Failed', str(failed_trans))
        self.assertIn('1000000002', str(failed_trans))

    def test_failed_transaction_ordering(self):
        failed1 = FailedTransaction.objects.create(
            account=self.account,
            attempted_amount=1000.00,
            attempted_transaction_type=WITHDRAWAL,
            failure_reason='Reason 1'
        )
        failed2 = FailedTransaction.objects.create(
            account=self.account,
            attempted_amount=2000.00,
            attempted_transaction_type=WITHDRAWAL,
            failure_reason='Reason 2'
        )
        failed_transactions = FailedTransaction.objects.all()
        self.assertEqual(failed_transactions[0], failed2)
        self.assertEqual(failed_transactions[1], failed1)


class DepositFormTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='deposit@example.com',
            password='testpass123'
        )
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=5000,
            annual_interest_rate=5.0,
            interest_calculation_per_year=12
        )
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000003,
            gender=MALE,
            birth_date=date(1990, 1, 1),
            balance=1000.00
        )

    def test_deposit_form_valid_amount(self):
        form_data = {
            'amount': settings.MINIMUM_DEPOSIT_AMOUNT,
            'transaction_type': DEPOSIT
        }
        form = DepositForm(data=form_data, account=self.account)
        self.assertTrue(form.is_valid())

    def test_deposit_form_below_minimum(self):
        form_data = {
            'amount': settings.MINIMUM_DEPOSIT_AMOUNT - 1,
            'transaction_type': DEPOSIT
        }
        form = DepositForm(data=form_data, account=self.account)
        self.assertFalse(form.is_valid())
        self.assertIn('amount', form.errors)

    def test_deposit_form_large_amount(self):
        form_data = {
            'amount': 100000.00,
            'transaction_type': DEPOSIT
        }
        form = DepositForm(data=form_data, account=self.account)
        self.assertTrue(form.is_valid())


class WithdrawFormTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='withdraw@example.com',
            password='testpass123'
        )
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=5000,
            annual_interest_rate=5.0,
            interest_calculation_per_year=12
        )
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000004,
            gender=MALE,
            birth_date=date(1990, 1, 1),
            balance=10000.00
        )

    def test_withdraw_form_valid_amount(self):
        form_data = {
            'amount': 100.00,
            'transaction_type': WITHDRAWAL
        }
        form = WithdrawForm(data=form_data, account=self.account)
        self.assertTrue(form.is_valid())

    def test_withdraw_form_below_minimum(self):
        form_data = {
            'amount': settings.MINIMUM_WITHDRAWAL_AMOUNT - 1,
            'transaction_type': WITHDRAWAL
        }
        form = WithdrawForm(data=form_data, account=self.account)
        self.assertFalse(form.is_valid())
        self.assertIn('amount', form.errors)

    def test_withdraw_form_above_maximum(self):
        form_data = {
            'amount': self.account_type.maximum_withdrawal_amount + 1,
            'transaction_type': WITHDRAWAL
        }
        form = WithdrawForm(data=form_data, account=self.account)
        self.assertFalse(form.is_valid())
        self.assertIn('amount', form.errors)

    def test_withdraw_form_at_maximum(self):
        form_data = {
            'amount': self.account_type.maximum_withdrawal_amount,
            'transaction_type': WITHDRAWAL
        }
        form = WithdrawForm(data=form_data, account=self.account)
        self.assertTrue(form.is_valid())


class TransactionDateRangeFormTest(TestCase):
    def test_valid_date_range(self):
        form_data = {
            'daterange': '2024-01-01 - 2024-01-31'
        }
        form = TransactionDateRangeForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['daterange'], ['2024-01-01', '2024-01-31'])

    def test_invalid_date_range_format(self):
        form_data = {
            'daterange': '2024-01-01'
        }
        form = TransactionDateRangeForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_invalid_date_format(self):
        form_data = {
            'daterange': '01/01/2024 - 31/01/2024'
        }
        form = TransactionDateRangeForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_empty_date_range(self):
        form_data = {
            'daterange': ''
        }
        form = TransactionDateRangeForm(data=form_data)
        self.assertTrue(form.is_valid())


class DepositMoneyViewTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.demo_user = User.objects.create_user(
            email='demo@example.com',
            password='testpass123'
        )
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=5000,
            annual_interest_rate=5.0,
            interest_calculation_per_year=12
        )
        self.account = UserBankAccount.objects.create(
            user=self.demo_user,
            account_type=self.account_type,
            account_no=1000000005,
            gender=MALE,
            birth_date=date(1990, 1, 1),
            balance=1000.00
        )

    def test_deposit_increases_balance(self):
        initial_balance = self.account.balance
        form_data = {
            'amount': 500.00,
            'transaction_type': DEPOSIT
        }
        request = self.factory.post('/deposit/', data=form_data)
        setattr(request, 'session', {})
        setattr(request, '_messages', FallbackStorage(request))
        
        view = DepositMoneyView()
        view.request = request
        form = DepositForm(data=form_data, account=self.account)
        self.assertTrue(form.is_valid())
        
        self.account.balance += form.cleaned_data['amount']
        self.account.save()
        
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, initial_balance + Decimal('500.00'))

    def test_first_deposit_sets_initial_date(self):
        new_user = User.objects.create_user(
            email='newuser@example.com',
            password='testpass123'
        )
        new_account = UserBankAccount.objects.create(
            user=new_user,
            account_type=self.account_type,
            account_no=1000000006,
            gender=MALE,
            birth_date=date(1990, 1, 1),
            balance=0
        )
        self.assertIsNone(new_account.initial_deposit_date)
        
        now = timezone.now()
        new_account.initial_deposit_date = now
        next_interest_month = int(12 / self.account_type.interest_calculation_per_year)
        new_account.interest_start_date = now + timedelta(days=30*next_interest_month)
        new_account.balance = 100.00
        new_account.save()
        
        new_account.refresh_from_db()
        self.assertIsNotNone(new_account.initial_deposit_date)
        self.assertIsNotNone(new_account.interest_start_date)


class WithdrawMoneyViewTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.demo_user = User.objects.create_user(
            email='demo@example.com',
            password='testpass123'
        )
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=5000,
            annual_interest_rate=5.0,
            interest_calculation_per_year=12
        )
        self.account = UserBankAccount.objects.create(
            user=self.demo_user,
            account_type=self.account_type,
            account_no=1000000007,
            gender=MALE,
            birth_date=date(1990, 1, 1),
            balance=5000.00
        )

    def test_withdraw_decreases_balance(self):
        initial_balance = self.account.balance
        form_data = {
            'amount': 500.00,
            'transaction_type': WITHDRAWAL
        }
        request = self.factory.post('/withdraw/', data=form_data)
        setattr(request, 'session', {})
        setattr(request, '_messages', FallbackStorage(request))
        
        form = WithdrawForm(data=form_data, account=self.account)
        self.assertTrue(form.is_valid())
        
        self.account.balance -= form.cleaned_data['amount']
        self.account.save()
        
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, initial_balance - Decimal('500.00'))


class TransactionReportViewTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.demo_user = User.objects.create_user(
            email='demo@example.com',
            password='testpass123'
        )
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=5000,
            annual_interest_rate=5.0,
            interest_calculation_per_year=12
        )
        self.account = UserBankAccount.objects.create(
            user=self.demo_user,
            account_type=self.account_type,
            account_no=1000000008,
            gender=MALE,
            birth_date=date(1990, 1, 1),
            balance=1000.00
        )
        Transaction.objects.create(
            account=self.account,
            amount=100.00,
            balance_after_transaction=1100.00,
            transaction_type=DEPOSIT
        )
        Transaction.objects.create(
            account=self.account,
            amount=50.00,
            balance_after_transaction=1050.00,
            transaction_type=WITHDRAWAL
        )

    def test_transaction_report_shows_all_transactions(self):
        request = self.factory.get('/transactions/')
        view = TransactionRepostView()
        view.request = request
        view.form_data = {}
        
        queryset = Transaction.objects.filter(account=self.account)
        self.assertEqual(queryset.count(), 2)


class CalculateInterestTaskTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='interest@example.com',
            password='testpass123'
        )
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=5000,
            annual_interest_rate=12.0,
            interest_calculation_per_year=12
        )

    @patch('transactions.tasks.timezone')
    def test_calculate_interest_creates_transactions(self, mock_timezone):
        mock_now = datetime(2024, 3, 15, tzinfo=timezone.get_current_timezone())
        mock_timezone.now.return_value = mock_now
        
        account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000009,
            gender=MALE,
            birth_date=date(1990, 1, 1),
            balance=1000.00,
            initial_deposit_date=date(2024, 1, 1),
            interest_start_date=date(2024, 3, 1)
        )
        
        initial_balance = account.balance
        expected_interest = self.account_type.calculate_interest(initial_balance)
        
        calculate_interest()
        
        account.refresh_from_db()
        self.assertEqual(account.balance, initial_balance + expected_interest)
        
        interest_transactions = Transaction.objects.filter(
            account=account,
            transaction_type=INTEREST
        )
        self.assertEqual(interest_transactions.count(), 1)
        self.assertEqual(interest_transactions.first().amount, expected_interest)

    @patch('transactions.tasks.timezone')
    def test_calculate_interest_skips_zero_balance(self, mock_timezone):
        mock_now = datetime(2024, 3, 15, tzinfo=timezone.get_current_timezone())
        mock_timezone.now.return_value = mock_now
        
        account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000010,
            gender=MALE,
            birth_date=date(1990, 1, 1),
            balance=0,
            initial_deposit_date=date(2024, 1, 1),
            interest_start_date=date(2024, 3, 1)
        )
        
        calculate_interest()
        
        interest_transactions = Transaction.objects.filter(
            account=account,
            transaction_type=INTEREST
        )
        self.assertEqual(interest_transactions.count(), 0)


class IPCaptureMiddlewareTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = IPCaptureMiddleware(lambda request: Mock(status_code=200))

    def test_middleware_sets_client_ip(self):
        request = self.factory.get('/')
        response = self.middleware(request)
        self.assertTrue(hasattr(request, 'client_ip'))
        self.assertIsNotNone(request.client_ip)

    def test_middleware_handles_unknown_ip(self):
        request = self.factory.get('/')
        response = self.middleware(request)
        self.assertIn(request.client_ip, ['127.0.0.1', 'unknown'])
