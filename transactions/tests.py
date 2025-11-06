from decimal import Decimal
from datetime import date
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.contrib.messages.storage.fallback import FallbackStorage
from django.conf import settings

from accounts.models import BankAccountType, UserBankAccount
from transactions.models import Transaction
from transactions.forms import DepositForm, WithdrawForm
from transactions.views import DepositMoneyView, WithdrawMoneyView
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
            email='test@example.com',
            password='testpass123'
        )
        self.bank_account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender='M',
            balance=Decimal('1000.00')
        )

    def test_transaction_creation(self):
        transaction = Transaction.objects.create(
            account=self.bank_account,
            amount=Decimal('100.00'),
            balance_after_transaction=Decimal('1100.00'),
            transaction_type=DEPOSIT
        )
        self.assertEqual(transaction.account, self.bank_account)
        self.assertEqual(transaction.amount, Decimal('100.00'))
        self.assertEqual(transaction.balance_after_transaction, Decimal('1100.00'))
        self.assertEqual(transaction.transaction_type, DEPOSIT)

    def test_transaction_string_representation(self):
        transaction = Transaction.objects.create(
            account=self.bank_account,
            amount=Decimal('50.00'),
            balance_after_transaction=Decimal('1050.00'),
            transaction_type=DEPOSIT
        )
        self.assertEqual(str(transaction), '1000000001')

    def test_transaction_ordering(self):
        transaction1 = Transaction.objects.create(
            account=self.bank_account,
            amount=Decimal('100.00'),
            balance_after_transaction=Decimal('1100.00'),
            transaction_type=DEPOSIT
        )
        transaction2 = Transaction.objects.create(
            account=self.bank_account,
            amount=Decimal('50.00'),
            balance_after_transaction=Decimal('1150.00'),
            transaction_type=DEPOSIT
        )
        transactions = Transaction.objects.all()
        self.assertEqual(transactions[0], transaction1)
        self.assertEqual(transactions[1], transaction2)


class DepositFormTests(TestCase):
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
            gender='M',
            balance=Decimal('500.00')
        )

    def test_deposit_form_valid_amount(self):
        form = DepositForm(
            data={'amount': Decimal('100.00')},
            initial={'transaction_type': DEPOSIT},
            account=self.bank_account
        )
        self.assertTrue(form.is_valid())

    def test_deposit_form_minimum_amount_validation(self):
        form = DepositForm(
            data={'amount': Decimal('5.00')},
            initial={'transaction_type': DEPOSIT},
            account=self.bank_account
        )
        self.assertFalse(form.is_valid())
        self.assertIn('amount', form.errors)

    def test_deposit_form_saves_with_balance_snapshot(self):
        form = DepositForm(
            data={'amount': Decimal('100.00')},
            initial={'transaction_type': DEPOSIT},
            account=self.bank_account
        )
        self.assertTrue(form.is_valid())
        transaction = form.save()
        self.assertEqual(transaction.balance_after_transaction, self.bank_account.balance)


class WithdrawFormTests(TestCase):
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
            gender='M',
            balance=Decimal('1000.00')
        )

    def test_withdraw_form_valid_amount(self):
        form = WithdrawForm(
            data={'amount': Decimal('100.00')},
            initial={'transaction_type': WITHDRAWAL},
            account=self.bank_account
        )
        self.assertTrue(form.is_valid())

    def test_withdraw_form_minimum_amount_validation(self):
        form = WithdrawForm(
            data={'amount': Decimal('5.00')},
            initial={'transaction_type': WITHDRAWAL},
            account=self.bank_account
        )
        self.assertFalse(form.is_valid())
        self.assertIn('amount', form.errors)

    def test_withdraw_form_maximum_amount_validation(self):
        form = WithdrawForm(
            data={'amount': Decimal('6000.00')},
            initial={'transaction_type': WITHDRAWAL},
            account=self.bank_account
        )
        self.assertFalse(form.is_valid())
        self.assertIn('amount', form.errors)

    def test_withdraw_allows_negative_balance_bug(self):
        """
        KNOWN BUG: Withdrawal form does not validate against account balance.
        This test demonstrates that users can withdraw more than their balance,
        resulting in negative balances. See transactions/forms.py lines 67-68.
        """
        self.bank_account.balance = Decimal('100.00')
        self.bank_account.save()
        
        form = WithdrawForm(
            data={'amount': Decimal('150.00')},
            initial={'transaction_type': WITHDRAWAL},
            account=self.bank_account
        )
        self.assertTrue(form.is_valid())


class DepositMoneyViewTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
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
            gender='M',
            balance=Decimal('0.00')
        )

    def test_deposit_increases_balance(self):
        initial_balance = self.bank_account.balance
        request = self.factory.post('/transactions/deposit/', {
            'amount': Decimal('500.00'),
            'transaction_type': DEPOSIT
        })
        request.user = self.demo_user
        setattr(request, 'session', {})
        setattr(request, '_messages', FallbackStorage(request))
        
        view = DepositMoneyView.as_view()
        response = view(request)
        
        self.bank_account.refresh_from_db()
        self.assertEqual(self.bank_account.balance, initial_balance + Decimal('500.00'))

    def test_first_deposit_sets_dates(self):
        self.assertIsNone(self.bank_account.initial_deposit_date)
        self.assertIsNone(self.bank_account.interest_start_date)
        
        request = self.factory.post('/transactions/deposit/', {
            'amount': Decimal('100.00'),
            'transaction_type': DEPOSIT
        })
        request.user = self.demo_user
        setattr(request, 'session', {})
        setattr(request, '_messages', FallbackStorage(request))
        
        view = DepositMoneyView.as_view()
        response = view(request)
        
        self.bank_account.refresh_from_db()
        self.assertIsNotNone(self.bank_account.initial_deposit_date)
        self.assertIsNotNone(self.bank_account.interest_start_date)


class WithdrawMoneyViewTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
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
            gender='M',
            balance=Decimal('1000.00')
        )

    def test_withdrawal_decreases_balance(self):
        initial_balance = self.bank_account.balance
        request = self.factory.post('/transactions/withdraw/', {
            'amount': Decimal('200.00'),
            'transaction_type': WITHDRAWAL
        })
        request.user = self.demo_user
        setattr(request, 'session', {})
        setattr(request, '_messages', FallbackStorage(request))
        
        view = WithdrawMoneyView.as_view()
        response = view(request)
        
        self.bank_account.refresh_from_db()
        self.assertEqual(self.bank_account.balance, initial_balance - Decimal('200.00'))

    def test_withdrawal_creates_negative_balance_bug(self):
        """
        KNOWN BUG: Withdrawal view does not prevent negative balances.
        This test demonstrates that withdrawals exceeding the balance are allowed,
        resulting in negative account balances.
        """
        self.bank_account.balance = Decimal('100.00')
        self.bank_account.save()
        
        request = self.factory.post('/transactions/withdraw/', {
            'amount': Decimal('150.00'),
            'transaction_type': WITHDRAWAL
        })
        request.user = self.demo_user
        setattr(request, 'session', {})
        setattr(request, '_messages', FallbackStorage(request))
        
        view = WithdrawMoneyView.as_view()
        response = view(request)
        
        self.bank_account.refresh_from_db()
        self.assertEqual(self.bank_account.balance, Decimal('-50.00'))
