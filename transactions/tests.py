from decimal import Decimal
from unittest.mock import Mock
import datetime

from django.test import TestCase, RequestFactory
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.conf import settings
from django import forms as django_forms

from accounts.models import BankAccountType, UserBankAccount
from transactions.models import Transaction, FailedTransaction
from transactions.forms import (
    TransactionDateRangeForm,
    DepositForm,
    WithdrawForm,
    TransactionForm,
)
from transactions.constants import DEPOSIT, WITHDRAWAL, INTEREST


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


class TransactionDateRangeFormTest(TransactionTestCase):
    
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


class DepositFormTest(TransactionTestCase):
    
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


class WithdrawFormTest(TransactionTestCase):
    
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


class TransactionModelTest(TransactionTestCase):
    
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


class FailedTransactionModelTest(TransactionTestCase):
    
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


class TransactionRepostViewTest(TransactionTestCase):
    
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
            timestamp=datetime.datetime(2024, 1, 15, 12, 0, 0)
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
        ).update(timestamp=datetime.datetime(2024, 2, 15, 12, 0, 0))
        
        view = TransactionRepostView()
        view.form_data = {'daterange': ['2024-01-01', '2024-01-31']}
        
        queryset = view.get_queryset()
        
        self.assertEqual(queryset.count(), 2)
