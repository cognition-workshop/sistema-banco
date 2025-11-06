from decimal import Decimal
from datetime import date, datetime, timedelta
from unittest.mock import patch, Mock

from django.test import TestCase, RequestFactory
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils import timezone
from django.contrib.messages.storage.fallback import FallbackStorage
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from accounts.models import BankAccountType, UserBankAccount
from accounts.constants import MALE
from transactions.models import Transaction, FailedTransaction
from transactions.forms import (
    TransactionDateRangeForm,
    DepositForm,
    WithdrawForm,
    TransactionForm,
)
from transactions.views import DepositMoneyView, WithdrawMoneyView, TransactionRepostView
from transactions.tasks import calculate_interest
from transactions.serializers import TransactionSerializer
from transactions.constants import DEPOSIT, WITHDRAWAL, INTEREST
from banking_system.middleware import IPCaptureMiddleware

User = get_user_model()


class TransactionTestCase(TestCase):
    
    def setUp(self):
        self.account_type = BankAccountType.objects.create(
            name='Savings Account',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('5.0'),
            interest_calculation_per_year=12
        )
        
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            agencia='0001',
            conta_digito='01',
            gender='M',
            balance=Decimal('1000.00')
        )
        
        self.demo_user = User.objects.create_user(
            email='demo@example.com',
            password='demopass123'
        )
        
        self.demo_account = UserBankAccount.objects.create(
            user=self.demo_user,
            account_type=self.account_type,
            account_no=1000000002,
            agencia='0001',
            conta_digito='02',
            gender='F',
            balance=Decimal('2000.00')
        )
        
        self.factory = RequestFactory()


class DateRangeFormValidationTest(TransactionTestCase):
    
    def test_clean_daterange_valid_format(self):
        form_data = {'daterange': '2024-01-01 - 2024-01-31'}
        form = TransactionDateRangeForm(data=form_data)
        
        is_valid = form.is_valid()
        
        self.assertTrue(is_valid)
        self.assertEqual(form.cleaned_data['daterange'], ['2024-01-01', '2024-01-31'])
    
    def test_clean_daterange_empty_is_valid(self):
        form_data = {'daterange': ''}
        form = TransactionDateRangeForm(data=form_data)
        
        is_valid = form.is_valid()
        
        self.assertTrue(is_valid)
    
    def test_clean_daterange_invalid_format_single_date(self):
        form_data = {'daterange': '2024-01-01'}
        form = TransactionDateRangeForm(data=form_data)
        
        is_valid = form.is_valid()
        
        self.assertFalse(is_valid)
        self.assertIn('daterange', form.errors)
        self.assertIn('Please select a date range', str(form.errors['daterange']))
    
    def test_clean_daterange_invalid_date_format(self):
        form_data = {'daterange': '01/01/2024 - 01/31/2024'}
        form = TransactionDateRangeForm(data=form_data)
        
        is_valid = form.is_valid()
        
        self.assertFalse(is_valid)
        self.assertIn('daterange', form.errors)
        self.assertIn('Invalid date range', str(form.errors['daterange']))
    
    def test_clean_daterange_invalid_date_values(self):
        form_data = {'daterange': '2024-13-45 - 2024-14-50'}
        form = TransactionDateRangeForm(data=form_data)
        
        is_valid = form.is_valid()
        
        self.assertFalse(is_valid)
        self.assertIn('daterange', form.errors)


class DepositFormValidationTest(TransactionTestCase):
    
    def test_clean_amount_valid_deposit(self):
        form_data = {
            'amount': Decimal('100.00'),
            'transaction_type': DEPOSIT
        }
        form = DepositForm(data=form_data, account=self.account)
        
        is_valid = form.is_valid()
        
        self.assertTrue(is_valid)
        self.assertEqual(form.cleaned_data['amount'], Decimal('100.00'))
    
    def test_clean_amount_minimum_deposit_exactly(self):
        form_data = {
            'amount': Decimal('10.00'),
            'transaction_type': DEPOSIT
        }
        form = DepositForm(data=form_data, account=self.account)
        
        is_valid = form.is_valid()
        
        self.assertTrue(is_valid)
    
    def test_clean_amount_below_minimum_creates_failed_transaction(self):
        form_data = {
            'amount': Decimal('5.00'),
            'transaction_type': DEPOSIT
        }
        form = DepositForm(data=form_data, account=self.account)
        initial_failed_count = FailedTransaction.objects.count()
        
        is_valid = form.is_valid()
        
        self.assertFalse(is_valid)
        self.assertIn('amount', form.errors)
        self.assertIn('at least 10', str(form.errors['amount']))
        self.assertEqual(FailedTransaction.objects.count(), initial_failed_count + 1)
        failed_trans = FailedTransaction.objects.latest('timestamp')
        self.assertEqual(failed_trans.account, self.account)
        self.assertEqual(failed_trans.attempted_amount, Decimal('5.00'))
        self.assertEqual(failed_trans.attempted_transaction_type, DEPOSIT)


class WithdrawFormValidationTest(TransactionTestCase):
    
    def test_clean_amount_valid_withdrawal(self):
        form_data = {
            'amount': Decimal('100.00'),
            'transaction_type': WITHDRAWAL
        }
        form = WithdrawForm(data=form_data, account=self.account)
        
        is_valid = form.is_valid()
        
        self.assertTrue(is_valid)
        self.assertEqual(form.cleaned_data['amount'], Decimal('100.00'))
    
    def test_clean_amount_below_minimum_creates_failed_transaction(self):
        form_data = {
            'amount': Decimal('5.00'),
            'transaction_type': WITHDRAWAL
        }
        form = WithdrawForm(data=form_data, account=self.account)
        initial_failed_count = FailedTransaction.objects.count()
        
        is_valid = form.is_valid()
        
        self.assertFalse(is_valid)
        self.assertIn('at least 10', str(form.errors['amount']))
        self.assertEqual(FailedTransaction.objects.count(), initial_failed_count + 1)
    
    def test_clean_amount_above_maximum_creates_failed_transaction(self):
        form_data = {
            'amount': Decimal('6000.00'),
            'transaction_type': WITHDRAWAL
        }
        form = WithdrawForm(data=form_data, account=self.account)
        initial_failed_count = FailedTransaction.objects.count()
        
        is_valid = form.is_valid()
        
        self.assertFalse(is_valid)
        self.assertIn('at most 5000', str(form.errors['amount']))
        self.assertEqual(FailedTransaction.objects.count(), initial_failed_count + 1)
    
    def test_clean_amount_exceeds_balance_creates_failed_transaction(self):
        form_data = {
            'amount': Decimal('2000.00'),
            'transaction_type': WITHDRAWAL
        }
        form = WithdrawForm(data=form_data, account=self.account)
        initial_failed_count = FailedTransaction.objects.count()
        
        is_valid = form.is_valid()
        
        self.assertFalse(is_valid)
        self.assertIn('Insufficient balance', str(form.errors['amount']))
        self.assertEqual(FailedTransaction.objects.count(), initial_failed_count + 1)
    
    def test_clean_amount_exactly_balance_passes(self):
        form_data = {
            'amount': Decimal('1000.00'),
            'transaction_type': WITHDRAWAL
        }
        form = WithdrawForm(data=form_data, account=self.account)
        
        is_valid = form.is_valid()
        
        self.assertTrue(is_valid)


class TransactionFormAuditTest(TransactionTestCase):
    
    def test_save_with_request_captures_ip_address(self):
        request = self.factory.get('/')
        request.client_ip = '192.168.1.1'
        request.META['HTTP_USER_AGENT'] = 'Mozilla/5.0'
        
        form_data = {
            'amount': Decimal('100.00'),
            'transaction_type': DEPOSIT
        }
        form = DepositForm(data=form_data, account=self.account, request=request)
        form.is_valid()
        
        transaction = form.save()
        
        self.assertEqual(transaction.ip_address, '192.168.1.1')
    
    def test_save_without_request_sets_system_values(self):
        form_data = {
            'amount': Decimal('100.00'),
            'transaction_type': DEPOSIT
        }
        form = DepositForm(data=form_data, account=self.account)
        form.is_valid()
        
        transaction = form.save()
        
        self.assertEqual(transaction.ip_address, 'system')
        self.assertEqual(transaction.geolocation, 'N/A')
        self.assertEqual(transaction.channel, 'system')
    
    def test_save_detects_web_channel(self):
        request = self.factory.get('/')
        request.client_ip = '192.168.1.1'
        request.META['HTTP_USER_AGENT'] = 'Mozilla/5.0 (Windows NT 10.0)'
        
        form_data = {
            'amount': Decimal('100.00'),
            'transaction_type': DEPOSIT
        }
        form = DepositForm(data=form_data, account=self.account, request=request)
        form.is_valid()
        
        transaction = form.save()
        
        self.assertEqual(transaction.channel, 'web')
    
    def test_save_detects_mobile_channel(self):
        request = self.factory.get('/')
        request.client_ip = '192.168.1.1'
        request.META['HTTP_USER_AGENT'] = 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0)'
        
        form_data = {
            'amount': Decimal('100.00'),
            'transaction_type': DEPOSIT
        }
        form = DepositForm(data=form_data, account=self.account, request=request)
        form.is_valid()
        
        transaction = form.save()
        
        self.assertEqual(transaction.channel, 'mobile')
    
    def test_save_detects_api_channel(self):
        request = self.factory.get('/')
        request.client_ip = '192.168.1.1'
        request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        request.META['HTTP_USER_AGENT'] = 'Mozilla/5.0'
        
        form_data = {
            'amount': Decimal('100.00'),
            'transaction_type': DEPOSIT
        }
        form = DepositForm(data=form_data, account=self.account, request=request)
        form.is_valid()
        
        transaction = form.save()
        
        self.assertEqual(transaction.channel, 'api')
    
    def test_save_generates_hash_signature(self):
        form_data = {
            'amount': Decimal('100.00'),
            'transaction_type': DEPOSIT
        }
        form = DepositForm(data=form_data, account=self.account)
        form.is_valid()
        
        transaction = form.save()
        
        self.assertIsNotNone(transaction.hash_signature)
        self.assertEqual(len(transaction.hash_signature), 64)


class TransactionModelImmutabilityTest(TransactionTestCase):
    
    def test_create_transaction_succeeds(self):
        initial_count = Transaction.objects.count()
        
        transaction = Transaction.objects.create(
            account=self.account,
            amount=Decimal('100.00'),
            balance_after_transaction=Decimal('1100.00'),
            transaction_type=DEPOSIT
        )
        
        self.assertEqual(Transaction.objects.count(), initial_count + 1)
        self.assertEqual(transaction.account, self.account)
        self.assertEqual(transaction.amount, Decimal('100.00'))
    
    def test_update_transaction_raises_validation_error(self):
        transaction = Transaction.objects.create(
            account=self.account,
            amount=Decimal('100.00'),
            balance_after_transaction=Decimal('1100.00'),
            transaction_type=DEPOSIT
        )
        
        transaction.amount = Decimal('200.00')
        with self.assertRaises(ValidationError) as context:
            transaction.save()
        
        self.assertIn('não podem ser modificadas', str(context.exception))
    
    def test_delete_transaction_raises_validation_error(self):
        transaction = Transaction.objects.create(
            account=self.account,
            amount=Decimal('100.00'),
            balance_after_transaction=Decimal('1100.00'),
            transaction_type=DEPOSIT
        )
        
        with self.assertRaises(ValidationError) as context:
            transaction.delete()
        
        self.assertIn('não podem ser deletadas', str(context.exception))


class FailedTransactionCreationTest(TransactionTestCase):
    
    def test_create_failed_transaction_succeeds(self):
        initial_count = FailedTransaction.objects.count()
        
        failed_trans = FailedTransaction.objects.create(
            account=self.account,
            attempted_amount=Decimal('5.00'),
            attempted_transaction_type=DEPOSIT,
            failure_reason='Amount below minimum'
        )
        
        self.assertEqual(FailedTransaction.objects.count(), initial_count + 1)
        self.assertEqual(failed_trans.account, self.account)
        self.assertEqual(failed_trans.attempted_amount, Decimal('5.00'))
        self.assertEqual(failed_trans.failure_reason, 'Amount below minimum')


class TransactionReportViewFilteringTest(TransactionTestCase):
    
    def setUp(self):
        super().setUp()
        Transaction.objects.create(
            account=self.demo_account,
            amount=Decimal('100.00'),
            balance_after_transaction=Decimal('2100.00'),
            transaction_type=DEPOSIT
        )
        Transaction.objects.create(
            account=self.demo_account,
            amount=Decimal('50.00'),
            balance_after_transaction=Decimal('2050.00'),
            transaction_type=WITHDRAWAL
        )
    
    def test_get_queryset_without_date_filter_returns_all(self):
        from transactions.views import TransactionRepostView
        view = TransactionRepostView()
        view.form_data = {}
        
        queryset = view.get_queryset()
        
        self.assertEqual(queryset.count(), 2)
    
    def test_get_queryset_with_date_filter_returns_filtered(self):
        from transactions.views import TransactionRepostView
        
        Transaction.objects.filter(account=self.demo_account).update(
            timestamp=datetime(2024, 1, 15, 12, 0, 0)
        )
        Transaction.objects.create(
            account=self.demo_account,
            amount=Decimal('75.00'),
            balance_after_transaction=Decimal('2125.00'),
            transaction_type=DEPOSIT
        )
        Transaction.objects.filter(
            account=self.demo_account,
            amount=Decimal('75.00')
        ).update(timestamp=datetime(2024, 2, 15, 12, 0, 0))
        
        view = TransactionRepostView()
        view.form_data = {'daterange': ['2024-01-01', '2024-01-31']}
        
        queryset = view.get_queryset()
        
        self.assertEqual(queryset.count(), 2)



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
            balance=Decimal('1000.00')
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
            balance=Decimal('5000.00')
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
            balance=Decimal('1000.00'),
            initial_deposit_date=date(2024, 1, 1),
            interest_start_date=date(2024, 3, 1)
        )
        
        initial_balance = Decimal(str(account.balance))
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


class TransactionSerializerTest(TestCase):
    """Test TransactionSerializer"""
    
    def setUp(self):
        self.user = User.objects.create_user(email='test@example.com', password='testpass123')
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('2.50'),
            interest_calculation_per_year=12
        )
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender=MALE,
            balance=Decimal('1000.00')
        )
    
    def test_serialization_with_computed_fields(self):
        """Test serializing a Transaction with computed fields"""
        transaction = Transaction.objects.create(
            account=self.account,
            amount=Decimal('100.00'),
            balance_after_transaction=Decimal('1100.00'),
            transaction_type=DEPOSIT
        )
        
        serializer = TransactionSerializer(transaction)
        data = serializer.data
        
        self.assertEqual(Decimal(data['amount']), Decimal('100.00'))
        self.assertEqual(Decimal(data['balance_after_transaction']), Decimal('1100.00'))
        self.assertEqual(data['transaction_type'], DEPOSIT)
        self.assertEqual(data['transaction_type_display'], 'Deposit')
        self.assertEqual(data['account_no'], 1000000001)
    
    def test_all_fields_read_only(self):
        """Test that all fields are read-only"""
        data = {
            'amount': '200.00',
            'balance_after_transaction': '1200.00',
            'transaction_type': WITHDRAWAL
        }
        
        serializer = TransactionSerializer(data=data)
        self.assertFalse(serializer.is_valid())


class TransactionViewSetTest(APITestCase):
    """Test TransactionViewSet API endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('2.50'),
            interest_calculation_per_year=12
        )
        
        self.staff_user = User.objects.create_user(
            email='staff@example.com',
            password='staffpass123',
            is_staff=True
        )
        
        self.regular_user = User.objects.create_user(
            email='regular@example.com',
            password='regularpass123'
        )
        self.regular_account = UserBankAccount.objects.create(
            user=self.regular_user,
            account_type=self.account_type,
            account_no=1000000001,
            gender=MALE,
            balance=Decimal('1000.00')
        )
        
        self.other_user = User.objects.create_user(
            email='other@example.com',
            password='otherpass123'
        )
        self.other_account = UserBankAccount.objects.create(
            user=self.other_user,
            account_type=self.account_type,
            account_no=1000000002,
            gender=MALE,
            balance=Decimal('2000.00')
        )
        
        self.user_no_account = User.objects.create_user(
            email='noaccount@example.com',
            password='noaccountpass123'
        )
        
        self.transaction1 = Transaction.objects.create(
            account=self.regular_account,
            amount=Decimal('100.00'),
            balance_after_transaction=Decimal('1100.00'),
            transaction_type=DEPOSIT
        )
        self.transaction2 = Transaction.objects.create(
            account=self.regular_account,
            amount=Decimal('50.00'),
            balance_after_transaction=Decimal('1050.00'),
            transaction_type=WITHDRAWAL
        )
        self.transaction3 = Transaction.objects.create(
            account=self.other_account,
            amount=Decimal('200.00'),
            balance_after_transaction=Decimal('2200.00'),
            transaction_type=DEPOSIT
        )
    
    def test_unauthenticated_access_denied(self):
        """Test that unauthenticated users cannot access the API"""
        response = self.client.get('/api/transactions/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_staff_can_list_all_transactions(self):
        """Test that staff users can see all transactions"""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get('/api/transactions/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 3)
    
    def test_regular_user_can_only_list_their_transactions(self):
        """Test that regular users can only see their own transactions"""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get('/api/transactions/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        for transaction in response.data['results']:
            self.assertEqual(transaction['account_no'], 1000000001)
    
    def test_user_without_account_gets_empty_queryset(self):
        """Test that users without account get empty queryset"""
        self.client.force_authenticate(user=self.user_no_account)
        response = self.client.get('/api/transactions/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)
    
    def test_retrieve_transaction(self):
        """Test retrieving a specific transaction"""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(f'/api/transactions/{self.transaction1.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['account_no'], 1000000001)
        self.assertEqual(Decimal(response.data['amount']), Decimal('100.00'))
    
    def test_cannot_retrieve_other_user_transaction(self):
        """Test that users cannot retrieve other users' transactions"""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(f'/api/transactions/{self.transaction3.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_create_not_allowed(self):
        """Test that creating transactions is not allowed (read-only)"""
        self.client.force_authenticate(user=self.regular_user)
        data = {
            'account': self.regular_account.id,
            'amount': '50.00',
            'balance_after_transaction': '1150.00',
            'transaction_type': DEPOSIT
        }
        response = self.client.post('/api/transactions/', data)
        
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def test_update_not_allowed(self):
        """Test that updating transactions is not allowed (read-only)"""
        self.client.force_authenticate(user=self.regular_user)
        data = {'amount': '999.99'}
        response = self.client.patch(f'/api/transactions/{self.transaction1.id}/', data)
        
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def test_delete_not_allowed(self):
        """Test that deleting transactions is not allowed (read-only)"""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.delete(f'/api/transactions/{self.transaction1.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def test_ordering_by_timestamp(self):
        """Test ordering transactions by timestamp"""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get('/api/transactions/?ordering=-timestamp')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        self.assertEqual(results[0]['id'], self.transaction3.id)
    
    def test_ordering_by_amount(self):
        """Test ordering transactions by amount"""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get('/api/transactions/?ordering=amount')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        self.assertEqual(Decimal(results[0]['amount']), Decimal('50.00'))
    
    def test_search_by_account_no(self):
        """Test searching transactions by account number"""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get('/api/transactions/?search=1000000001')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        for transaction in response.data['results']:
            self.assertEqual(transaction['account_no'], 1000000001)
