from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from datetime import date

from accounts.models import BankAccountType, UserBankAccount
from transactions.models import Transaction
from transactions.constants import DEPOSIT, WITHDRAWAL
from transactions.forms import DepositForm, WithdrawForm, TransactionDateRangeForm
from django.conf import settings


User = get_user_model()


class TransactionModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('5.00'),
            interest_calculation_per_year=12
        )
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender='M',
            birth_date=date(1990, 1, 1),
            balance=Decimal('1000.00')
        )

    def test_create_transaction(self):
        transaction = Transaction.objects.create(
            account=self.account,
            amount=Decimal('100.00'),
            balance_after_transaction=Decimal('1100.00'),
            transaction_type=DEPOSIT
        )
        self.assertEqual(transaction.account, self.account)
        self.assertEqual(transaction.amount, Decimal('100.00'))
        self.assertEqual(transaction.balance_after_transaction, Decimal('1100.00'))
        self.assertEqual(transaction.transaction_type, DEPOSIT)

    def test_transaction_ordering(self):
        transaction1 = Transaction.objects.create(
            account=self.account,
            amount=Decimal('100.00'),
            balance_after_transaction=Decimal('1100.00'),
            transaction_type=DEPOSIT
        )
        transaction2 = Transaction.objects.create(
            account=self.account,
            amount=Decimal('50.00'),
            balance_after_transaction=Decimal('1150.00'),
            transaction_type=DEPOSIT
        )
        transactions = Transaction.objects.all()
        self.assertEqual(transactions[0], transaction1)
        self.assertEqual(transactions[1], transaction2)

    def test_transaction_string_representation(self):
        transaction = Transaction.objects.create(
            account=self.account,
            amount=Decimal('100.00'),
            balance_after_transaction=Decimal('1100.00'),
            transaction_type=DEPOSIT
        )
        self.assertEqual(str(transaction), str(self.account.account_no))


class DepositFormTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('5.00'),
            interest_calculation_per_year=12
        )
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender='M',
            birth_date=date(1990, 1, 1),
            balance=Decimal('500.00')
        )

    def test_deposit_form_minimum_amount_valid(self):
        form = DepositForm(
            data={'amount': Decimal('10.00')},
            initial={'transaction_type': DEPOSIT},
            account=self.account
        )
        self.assertTrue(form.is_valid())

    def test_deposit_form_minimum_amount_invalid(self):
        form = DepositForm(
            data={'amount': Decimal('5.00')},
            initial={'transaction_type': DEPOSIT},
            account=self.account
        )
        self.assertFalse(form.is_valid())
        self.assertIn('amount', form.errors)

    def test_deposit_form_saves_with_account(self):
        form = DepositForm(
            data={'amount': Decimal('100.00')},
            initial={'transaction_type': DEPOSIT},
            account=self.account
        )
        self.assertTrue(form.is_valid())
        transaction = form.save()
        self.assertEqual(transaction.account, self.account)
        self.assertEqual(transaction.amount, Decimal('100.00'))


class WithdrawFormTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('5.00'),
            interest_calculation_per_year=12
        )
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender='M',
            birth_date=date(1990, 1, 1),
            balance=Decimal('500.00')
        )

    def test_withdraw_form_minimum_amount_valid(self):
        form = WithdrawForm(
            data={'amount': Decimal('10.00')},
            initial={'transaction_type': WITHDRAWAL},
            account=self.account
        )
        self.assertTrue(form.is_valid())

    def test_withdraw_form_minimum_amount_invalid(self):
        form = WithdrawForm(
            data={'amount': Decimal('5.00')},
            initial={'transaction_type': WITHDRAWAL},
            account=self.account
        )
        self.assertFalse(form.is_valid())
        self.assertIn('amount', form.errors)

    def test_withdraw_form_maximum_amount_invalid(self):
        form = WithdrawForm(
            data={'amount': Decimal('6000.00')},
            initial={'transaction_type': WITHDRAWAL},
            account=self.account
        )
        self.assertFalse(form.is_valid())
        self.assertIn('amount', form.errors)

    def test_withdraw_form_allows_overdraft_bug(self):
        self.account.balance = Decimal('50.00')
        self.account.save()
        
        form = WithdrawForm(
            data={'amount': Decimal('100.00')},
            initial={'transaction_type': WITHDRAWAL},
            account=self.account
        )
        self.assertTrue(form.is_valid())


class TransactionDateRangeFormTest(TestCase):

    def test_valid_date_range(self):
        form = TransactionDateRangeForm(
            data={'daterange': '2024-01-01 - 2024-12-31'}
        )
        self.assertTrue(form.is_valid())

    def test_invalid_date_format(self):
        form = TransactionDateRangeForm(
            data={'daterange': 'invalid-date-range'}
        )
        self.assertFalse(form.is_valid())

    def test_empty_date_range(self):
        form = TransactionDateRangeForm(
            data={'daterange': ''}
        )
        self.assertFalse(form.is_valid())


class DepositMoneyViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='demo@example.com',
            password='testpass123'
        )
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('5.00'),
            interest_calculation_per_year=12
        )
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender='M',
            birth_date=date(1990, 1, 1),
            balance=Decimal('0.00')
        )

    def test_deposit_increases_balance(self):
        initial_balance = self.account.balance
        response = self.client.post(reverse('transactions:deposit_money'), {
            'amount': '100.00',
            'transaction_type': DEPOSIT
        })
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, initial_balance + Decimal('100.00'))

    def test_deposit_creates_transaction(self):
        initial_count = Transaction.objects.count()
        response = self.client.post(reverse('transactions:deposit_money'), {
            'amount': '100.00',
            'transaction_type': DEPOSIT
        })
        self.assertEqual(Transaction.objects.count(), initial_count + 1)

    def test_first_deposit_sets_initial_date(self):
        self.assertIsNone(self.account.initial_deposit_date)
        response = self.client.post(reverse('transactions:deposit_money'), {
            'amount': '100.00',
            'transaction_type': DEPOSIT
        })
        self.account.refresh_from_db()
        self.assertIsNotNone(self.account.initial_deposit_date)
        self.assertIsNotNone(self.account.interest_start_date)


class WithdrawMoneyViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='demo@example.com',
            password='testpass123'
        )
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('5.00'),
            interest_calculation_per_year=12
        )
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender='M',
            birth_date=date(1990, 1, 1),
            balance=Decimal('500.00')
        )

    def test_withdrawal_decreases_balance(self):
        initial_balance = self.account.balance
        response = self.client.post(reverse('transactions:withdraw_money'), {
            'amount': '100.00',
            'transaction_type': WITHDRAWAL
        })
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, initial_balance - Decimal('100.00'))

    def test_withdrawal_creates_transaction(self):
        initial_count = Transaction.objects.count()
        response = self.client.post(reverse('transactions:withdraw_money'), {
            'amount': '100.00',
            'transaction_type': WITHDRAWAL
        })
        self.assertEqual(Transaction.objects.count(), initial_count + 1)

    def test_withdrawal_allows_negative_balance_bug(self):
        self.account.balance = Decimal('50.00')
        self.account.save()
        
        response = self.client.post(reverse('transactions:withdraw_money'), {
            'amount': '100.00',
            'transaction_type': WITHDRAWAL
        })
        
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal('-50.00'))
