from decimal import Decimal
from datetime import date
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.conf import settings

from accounts.models import BankAccountType, UserBankAccount
from accounts.constants import MALE
from transactions.models import Transaction
from transactions.forms import DepositForm, WithdrawForm
from transactions.constants import DEPOSIT, WITHDRAWAL

User = get_user_model()


class TransactionModelTests(TestCase):
    def setUp(self):
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('5.00'),
            interest_calculation_per_year=12
        )
        self.user = User.objects.create_user(
            email='demo@example.com',
            password='testpass123'
        )
        self.bank_account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender=MALE,
            balance=Decimal('1000.00')
        )

    def test_create_deposit_transaction(self):
        transaction = Transaction.objects.create(
            account=self.bank_account,
            amount=Decimal('500.00'),
            balance_after_transaction=Decimal('1500.00'),
            transaction_type=DEPOSIT
        )
        self.assertEqual(transaction.account, self.bank_account)
        self.assertEqual(transaction.amount, Decimal('500.00'))
        self.assertEqual(transaction.transaction_type, DEPOSIT)

    def test_create_withdrawal_transaction(self):
        transaction = Transaction.objects.create(
            account=self.bank_account,
            amount=Decimal('200.00'),
            balance_after_transaction=Decimal('800.00'),
            transaction_type=WITHDRAWAL
        )
        self.assertEqual(transaction.amount, Decimal('200.00'))
        self.assertEqual(transaction.transaction_type, WITHDRAWAL)

    def test_transaction_ordering_by_timestamp(self):
        Transaction.objects.create(
            account=self.bank_account,
            amount=Decimal('100.00'),
            balance_after_transaction=Decimal('1100.00'),
            transaction_type=DEPOSIT
        )
        Transaction.objects.create(
            account=self.bank_account,
            amount=Decimal('50.00'),
            balance_after_transaction=Decimal('1150.00'),
            transaction_type=DEPOSIT
        )
        transactions = Transaction.objects.filter(account=self.bank_account)
        self.assertEqual(transactions.count(), 2)
        self.assertTrue(transactions[0].timestamp <= transactions[1].timestamp)


class DepositFormTests(TestCase):
    def setUp(self):
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('5.00'),
            interest_calculation_per_year=12
        )
        self.user = User.objects.create_user(
            email='demo@example.com',
            password='testpass123'
        )
        self.bank_account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender=MALE,
            balance=Decimal('1000.00')
        )

    def test_deposit_form_valid_amount(self):
        form = DepositForm(
            data={
                'amount': Decimal('100.00'),
            },
            account=self.bank_account,
            initial={'transaction_type': DEPOSIT}
        )
        self.assertTrue(form.is_valid())

    def test_deposit_form_rejects_amount_below_minimum(self):
        form = DepositForm(
            data={
                'amount': Decimal('5.00'),
            },
            account=self.bank_account,
            initial={'transaction_type': DEPOSIT}
        )
        self.assertFalse(form.is_valid())
        self.assertIn('amount', form.errors)

    def test_deposit_form_accepts_minimum_amount(self):
        form = DepositForm(
            data={
                'amount': Decimal(str(settings.MINIMUM_DEPOSIT_AMOUNT)),
            },
            account=self.bank_account,
            initial={'transaction_type': DEPOSIT}
        )
        self.assertTrue(form.is_valid())


class WithdrawFormTests(TestCase):
    def setUp(self):
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('5.00'),
            interest_calculation_per_year=12
        )
        self.user = User.objects.create_user(
            email='demo@example.com',
            password='testpass123'
        )
        self.bank_account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender=MALE,
            balance=Decimal('1000.00')
        )

    def test_withdraw_form_valid_amount(self):
        form = WithdrawForm(
            data={
                'amount': Decimal('500.00'),
            },
            account=self.bank_account,
            initial={'transaction_type': WITHDRAWAL}
        )
        self.assertTrue(form.is_valid())

    def test_withdraw_form_rejects_amount_below_minimum(self):
        form = WithdrawForm(
            data={
                'amount': Decimal('5.00'),
            },
            account=self.bank_account,
            initial={'transaction_type': WITHDRAWAL}
        )
        self.assertFalse(form.is_valid())
        self.assertIn('amount', form.errors)

    def test_withdraw_form_rejects_amount_above_maximum(self):
        form = WithdrawForm(
            data={
                'amount': Decimal('6000.00'),
            },
            account=self.bank_account,
            initial={'transaction_type': WITHDRAWAL}
        )
        self.assertFalse(form.is_valid())
        self.assertIn('amount', form.errors)

    def test_withdraw_form_allows_negative_balance_bug(self):
        form = WithdrawForm(
            data={
                'amount': Decimal('1500.00'),
            },
            account=self.bank_account,
            initial={'transaction_type': WITHDRAWAL}
        )
        self.assertTrue(form.is_valid())


class DepositMoneyViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('5.00'),
            interest_calculation_per_year=12
        )
        self.user = User.objects.create_user(
            email='demo@example.com',
            password='testpass123'
        )
        self.bank_account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender=MALE,
            balance=Decimal('0.00')
        )

    def test_deposit_increases_balance(self):
        initial_balance = self.bank_account.balance
        response = self.client.post(
            reverse('transactions:deposit_money'),
            {
                'amount': Decimal('500.00'),
                'transaction_type': DEPOSIT
            }
        )
        self.bank_account.refresh_from_db()
        self.assertEqual(self.bank_account.balance, initial_balance + Decimal('500.00'))

    def test_deposit_creates_transaction_record(self):
        self.client.post(
            reverse('transactions:deposit_money'),
            {
                'amount': Decimal('300.00'),
                'transaction_type': DEPOSIT
            }
        )
        transaction = Transaction.objects.filter(
            account=self.bank_account,
            transaction_type=DEPOSIT
        ).first()
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction.amount, Decimal('300.00'))

    def test_first_deposit_sets_initial_dates(self):
        self.assertIsNone(self.bank_account.initial_deposit_date)
        self.assertIsNone(self.bank_account.interest_start_date)
        self.client.post(
            reverse('transactions:deposit_money'),
            {
                'amount': Decimal('1000.00'),
                'transaction_type': DEPOSIT
            }
        )
        self.bank_account.refresh_from_db()
        self.assertIsNotNone(self.bank_account.initial_deposit_date)
        self.assertIsNotNone(self.bank_account.interest_start_date)


class WithdrawMoneyViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('5.00'),
            interest_calculation_per_year=12
        )
        self.user = User.objects.create_user(
            email='demo@example.com',
            password='testpass123'
        )
        self.bank_account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender=MALE,
            balance=Decimal('1000.00')
        )

    def test_withdrawal_decreases_balance(self):
        initial_balance = self.bank_account.balance
        response = self.client.post(
            reverse('transactions:withdraw_money'),
            {
                'amount': Decimal('200.00'),
                'transaction_type': WITHDRAWAL
            }
        )
        self.bank_account.refresh_from_db()
        self.assertEqual(self.bank_account.balance, initial_balance - Decimal('200.00'))

    def test_withdrawal_creates_transaction_record(self):
        self.client.post(
            reverse('transactions:withdraw_money'),
            {
                'amount': Decimal('150.00'),
                'transaction_type': WITHDRAWAL
            }
        )
        transaction = Transaction.objects.filter(
            account=self.bank_account,
            transaction_type=WITHDRAWAL
        ).first()
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction.amount, Decimal('150.00'))

    def test_withdrawal_allows_negative_balance_bug(self):
        initial_balance = self.bank_account.balance
        self.client.post(
            reverse('transactions:withdraw_money'),
            {
                'amount': Decimal('1500.00'),
                'transaction_type': WITHDRAWAL
            }
        )
        self.bank_account.refresh_from_db()
        self.assertLess(self.bank_account.balance, Decimal('0.00'))


class TransactionReportViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('5.00'),
            interest_calculation_per_year=12
        )
        self.user = User.objects.create_user(
            email='demo@example.com',
            password='testpass123'
        )
        self.bank_account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender=MALE,
            balance=Decimal('1000.00')
        )
        Transaction.objects.create(
            account=self.bank_account,
            amount=Decimal('500.00'),
            balance_after_transaction=Decimal('1500.00'),
            transaction_type=DEPOSIT
        )
        Transaction.objects.create(
            account=self.bank_account,
            amount=Decimal('200.00'),
            balance_after_transaction=Decimal('1300.00'),
            transaction_type=WITHDRAWAL
        )

    def test_transaction_report_displays_all_transactions(self):
        response = self.client.get(reverse('transactions:transaction_report'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 2)

    def test_transaction_report_filters_by_date_range(self):
        today = date.today()
        response = self.client.get(
            reverse('transactions:transaction_report'),
            {'daterange': f'{today} - {today}'}
        )
        self.assertEqual(response.status_code, 200)

    def test_transaction_report_returns_empty_for_nonexistent_user(self):
        User.objects.filter(email='demo@example.com').delete()
        response = self.client.get(reverse('transactions:transaction_report'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 0)
