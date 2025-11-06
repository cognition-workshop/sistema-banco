from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.conf import settings
from django.utils import timezone

from .models import Transaction
from .forms import DepositForm, WithdrawForm, TransactionDateRangeForm
from .constants import DEPOSIT, WITHDRAWAL, INTEREST
from accounts.models import BankAccountType, UserBankAccount
from accounts.constants import MALE


User = get_user_model()


class TransactionModelTest(TestCase):
    def setUp(self):
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('5.00'),
            interest_calculation_per_year=12
        )
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.bank_account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender=MALE,
            birth_date=date(1990, 1, 1),
            balance=Decimal('1000.00')
        )

    def test_transaction_creation_deposit(self):
        transaction = Transaction.objects.create(
            account=self.bank_account,
            amount=Decimal('500.00'),
            balance_after_transaction=Decimal('1500.00'),
            transaction_type=DEPOSIT
        )
        self.assertEqual(transaction.amount, Decimal('500.00'))
        self.assertEqual(transaction.transaction_type, DEPOSIT)
        self.assertEqual(transaction.balance_after_transaction, Decimal('1500.00'))

    def test_transaction_creation_withdrawal(self):
        transaction = Transaction.objects.create(
            account=self.bank_account,
            amount=Decimal('200.00'),
            balance_after_transaction=Decimal('800.00'),
            transaction_type=WITHDRAWAL
        )
        self.assertEqual(transaction.amount, Decimal('200.00'))
        self.assertEqual(transaction.transaction_type, WITHDRAWAL)
        self.assertEqual(transaction.balance_after_transaction, Decimal('800.00'))

    def test_transaction_creation_interest(self):
        transaction = Transaction.objects.create(
            account=self.bank_account,
            amount=Decimal('50.00'),
            balance_after_transaction=Decimal('1050.00'),
            transaction_type=INTEREST
        )
        self.assertEqual(transaction.transaction_type, INTEREST)

    def test_transaction_str_representation(self):
        transaction = Transaction.objects.create(
            account=self.bank_account,
            amount=Decimal('100.00'),
            balance_after_transaction=Decimal('1100.00'),
            transaction_type=DEPOSIT
        )
        self.assertEqual(str(transaction), str(self.bank_account.account_no))

    def test_transaction_ordering(self):
        trans1 = Transaction.objects.create(
            account=self.bank_account,
            amount=Decimal('100.00'),
            balance_after_transaction=Decimal('1100.00'),
            transaction_type=DEPOSIT
        )
        trans2 = Transaction.objects.create(
            account=self.bank_account,
            amount=Decimal('200.00'),
            balance_after_transaction=Decimal('1300.00'),
            transaction_type=DEPOSIT
        )
        transactions = Transaction.objects.all()
        self.assertEqual(transactions[0].id, trans1.id)
        self.assertEqual(transactions[1].id, trans2.id)

    def test_transaction_relationship_with_account(self):
        Transaction.objects.create(
            account=self.bank_account,
            amount=Decimal('100.00'),
            balance_after_transaction=Decimal('1100.00'),
            transaction_type=DEPOSIT
        )
        self.assertEqual(self.bank_account.transactions.count(), 1)


class DepositFormTest(TestCase):
    def setUp(self):
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('5.00'),
            interest_calculation_per_year=12
        )
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.bank_account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender=MALE,
            birth_date=date(1990, 1, 1),
            balance=Decimal('1000.00')
        )

    def test_valid_deposit(self):
        form_data = {
            'amount': Decimal('100.00'),
        }
        form = DepositForm(data=form_data, initial={'transaction_type': DEPOSIT}, account=self.bank_account)
        self.assertTrue(form.is_valid())

    def test_deposit_below_minimum(self):
        form_data = {
            'amount': Decimal('5.00'),
        }
        form = DepositForm(data=form_data, initial={'transaction_type': DEPOSIT}, account=self.bank_account)
        self.assertFalse(form.is_valid())
        self.assertIn('amount', form.errors)

    def test_deposit_at_minimum(self):
        form_data = {
            'amount': Decimal(str(settings.MINIMUM_DEPOSIT_AMOUNT)),
        }
        form = DepositForm(data=form_data, initial={'transaction_type': DEPOSIT}, account=self.bank_account)
        self.assertTrue(form.is_valid())

    def test_large_deposit(self):
        form_data = {
            'amount': Decimal('100000.00'),
        }
        form = DepositForm(data=form_data, initial={'transaction_type': DEPOSIT}, account=self.bank_account)
        self.assertTrue(form.is_valid())


class WithdrawFormTest(TestCase):
    def setUp(self):
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('5.00'),
            interest_calculation_per_year=12
        )
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.bank_account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender=MALE,
            birth_date=date(1990, 1, 1),
            balance=Decimal('1000.00')
        )

    def test_valid_withdrawal(self):
        form_data = {
            'amount': Decimal('500.00'),
        }
        form = WithdrawForm(data=form_data, initial={'transaction_type': WITHDRAWAL}, account=self.bank_account)
        self.assertTrue(form.is_valid())

    def test_withdrawal_below_minimum(self):
        form_data = {
            'amount': Decimal('5.00'),
        }
        form = WithdrawForm(data=form_data, initial={'transaction_type': WITHDRAWAL}, account=self.bank_account)
        self.assertFalse(form.is_valid())
        self.assertIn('amount', form.errors)

    def test_withdrawal_above_maximum(self):
        form_data = {
            'amount': Decimal('6000.00'),
        }
        form = WithdrawForm(data=form_data, initial={'transaction_type': WITHDRAWAL}, account=self.bank_account)
        self.assertFalse(form.is_valid())
        self.assertIn('amount', form.errors)

    def test_withdrawal_at_maximum(self):
        self.bank_account.balance = Decimal('10000.00')
        self.bank_account.save()
        
        form_data = {
            'amount': Decimal('5000.00'),
        }
        form = WithdrawForm(data=form_data, initial={'transaction_type': WITHDRAWAL}, account=self.bank_account)
        self.assertTrue(form.is_valid())

    def test_negative_balance_bug_withdrawal_exceeds_balance(self):
        form_data = {
            'amount': Decimal('1500.00'),
        }
        form = WithdrawForm(data=form_data, initial={'transaction_type': WITHDRAWAL}, account=self.bank_account)
        self.assertFalse(form.is_valid())
        self.assertIn('amount', form.errors)

    def test_withdrawal_equals_balance(self):
        form_data = {
            'amount': Decimal('1000.00'),
        }
        form = WithdrawForm(data=form_data, initial={'transaction_type': WITHDRAWAL}, account=self.bank_account)
        self.assertTrue(form.is_valid())


class TransactionDateRangeFormTest(TestCase):
    def test_valid_date_range(self):
        form_data = {
            'daterange': '2024-01-01 - 2024-01-31'
        }
        form = TransactionDateRangeForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['daterange'], ['2024-01-01', '2024-01-31'])

    def test_invalid_date_format(self):
        form_data = {
            'daterange': '01/01/2024 - 01/31/2024'
        }
        form = TransactionDateRangeForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_empty_date_range(self):
        form_data = {
            'daterange': ''
        }
        form = TransactionDateRangeForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_single_date(self):
        form_data = {
            'daterange': '2024-01-01'
        }
        form = TransactionDateRangeForm(data=form_data)
        self.assertFalse(form.is_valid())


class DepositMoneyViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('5.00'),
            interest_calculation_per_year=12
        )
        self.demo_user = User.objects.create_user(
            email='demo@example.com',
            password='demo123'
        )
        self.bank_account = UserBankAccount.objects.create(
            user=self.demo_user,
            account_type=self.account_type,
            account_no=1000000001,
            gender=MALE,
            birth_date=date(1990, 1, 1),
            balance=Decimal('0.00')
        )
        self.deposit_url = reverse('transactions:deposit_money')

    def test_first_deposit_sets_dates(self):
        form_data = {
            'amount': Decimal('100.00'),
        }
        response = self.client.post(self.deposit_url, form_data)
        
        self.bank_account.refresh_from_db()
        self.assertIsNotNone(self.bank_account.initial_deposit_date)
        self.assertIsNotNone(self.bank_account.interest_start_date)
        self.assertEqual(self.bank_account.balance, Decimal('100.00'))

    def test_deposit_updates_balance_correctly(self):
        self.bank_account.initial_deposit_date = timezone.now().date()
        self.bank_account.save()
        
        form_data = {
            'amount': Decimal('500.00'),
        }
        self.client.post(self.deposit_url, form_data)
        
        self.bank_account.refresh_from_db()
        self.assertEqual(self.bank_account.balance, Decimal('500.00'))

    def test_deposit_creates_transaction_record(self):
        form_data = {
            'amount': Decimal('200.00'),
        }
        self.client.post(self.deposit_url, form_data)
        
        transaction = Transaction.objects.filter(account=self.bank_account).first()
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction.amount, Decimal('200.00'))
        self.assertEqual(transaction.transaction_type, DEPOSIT)
        self.assertEqual(transaction.balance_after_transaction, Decimal('200.00'))

    def test_multiple_deposits_accumulate(self):
        self.bank_account.initial_deposit_date = timezone.now().date()
        self.bank_account.balance = Decimal('100.00')
        self.bank_account.save()
        
        form_data = {
            'amount': Decimal('50.00'),
        }
        self.client.post(self.deposit_url, form_data)
        
        self.bank_account.refresh_from_db()
        self.assertEqual(self.bank_account.balance, Decimal('150.00'))


class WithdrawMoneyViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('5.00'),
            interest_calculation_per_year=12
        )
        self.demo_user = User.objects.create_user(
            email='demo@example.com',
            password='demo123'
        )
        self.bank_account = UserBankAccount.objects.create(
            user=self.demo_user,
            account_type=self.account_type,
            account_no=1000000001,
            gender=MALE,
            birth_date=date(1990, 1, 1),
            balance=Decimal('1000.00')
        )
        self.withdraw_url = reverse('transactions:withdraw_money')

    def test_withdrawal_updates_balance_correctly(self):
        form_data = {
            'amount': Decimal('300.00'),
        }
        self.client.post(self.withdraw_url, form_data)
        
        self.bank_account.refresh_from_db()
        self.assertEqual(self.bank_account.balance, Decimal('700.00'))

    def test_withdrawal_creates_transaction_record(self):
        form_data = {
            'amount': Decimal('200.00'),
        }
        self.client.post(self.withdraw_url, form_data)
        
        transaction = Transaction.objects.filter(account=self.bank_account).first()
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction.amount, Decimal('200.00'))
        self.assertEqual(transaction.transaction_type, WITHDRAWAL)
        self.assertEqual(transaction.balance_after_transaction, Decimal('800.00'))

    def test_multiple_withdrawals_deduct(self):
        form_data = {
            'amount': Decimal('100.00'),
        }
        self.client.post(self.withdraw_url, form_data)
        
        self.bank_account.refresh_from_db()
        self.assertEqual(self.bank_account.balance, Decimal('900.00'))
        
        form_data['amount'] = Decimal('50.00')
        self.client.post(self.withdraw_url, form_data)
        
        self.bank_account.refresh_from_db()
        self.assertEqual(self.bank_account.balance, Decimal('850.00'))


class TransactionRepostViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('5.00'),
            interest_calculation_per_year=12
        )
        self.demo_user = User.objects.create_user(
            email='demo@example.com',
            password='demo123'
        )
        self.bank_account = UserBankAccount.objects.create(
            user=self.demo_user,
            account_type=self.account_type,
            account_no=1000000001,
            gender=MALE,
            birth_date=date(1990, 1, 1),
            balance=Decimal('1000.00')
        )
        self.report_url = reverse('transactions:transaction_report')

    def test_transaction_report_displays_all_transactions(self):
        Transaction.objects.create(
            account=self.bank_account,
            amount=Decimal('100.00'),
            balance_after_transaction=Decimal('1100.00'),
            transaction_type=DEPOSIT
        )
        Transaction.objects.create(
            account=self.bank_account,
            amount=Decimal('50.00'),
            balance_after_transaction=Decimal('1050.00'),
            transaction_type=WITHDRAWAL
        )
        
        response = self.client.get(self.report_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 2)

    def test_transaction_report_with_date_filter(self):
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        
        Transaction.objects.create(
            account=self.bank_account,
            amount=Decimal('100.00'),
            balance_after_transaction=Decimal('1100.00'),
            transaction_type=DEPOSIT
        )
        
        response = self.client.get(
            self.report_url,
            {'daterange': f'{yesterday} - {today}'}
        )
        self.assertEqual(response.status_code, 200)

    def test_transaction_report_without_demo_user(self):
        self.demo_user.delete()
        response = self.client.get(self.report_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 0)
