from decimal import Decimal
from datetime import date
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.contrib.messages.storage.fallback import FallbackStorage

from accounts.models import BankAccountType, UserBankAccount
from accounts.constants import MALE
from transactions.models import Transaction
from transactions.forms import DepositForm, WithdrawForm
from transactions.views import DepositMoneyView, WithdrawMoneyView
from transactions.constants import DEPOSIT, WITHDRAWAL

User = get_user_model()


class TransactionModelTests(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='trans@example.com',
            password='testpass123'
        )
        account_type = BankAccountType.objects.create(
            name='Checking',
            maximum_withdrawal_amount=Decimal('10000.00'),
            annual_interest_rate=Decimal('3.00'),
            interest_calculation_per_year=12
        )
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=account_type,
            account_no=1000000010,
            gender=MALE,
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
        self.assertEqual(transaction.transaction_type, DEPOSIT)
    
    def test_transaction_ordering(self):
        trans1 = Transaction.objects.create(
            account=self.account,
            amount=Decimal('50.00'),
            balance_after_transaction=Decimal('1050.00'),
            transaction_type=DEPOSIT
        )
        trans2 = Transaction.objects.create(
            account=self.account,
            amount=Decimal('25.00'),
            balance_after_transaction=Decimal('1075.00'),
            transaction_type=DEPOSIT
        )
        transactions = Transaction.objects.all()
        self.assertEqual(transactions[0], trans1)
        self.assertEqual(transactions[1], trans2)
    
    def test_transaction_string_representation(self):
        transaction = Transaction.objects.create(
            account=self.account,
            amount=Decimal('100.00'),
            balance_after_transaction=Decimal('1100.00'),
            transaction_type=DEPOSIT
        )
        self.assertEqual(str(transaction), '1000000010')


class DepositFormTests(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='deposit@example.com',
            password='testpass123'
        )
        account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('5.00'),
            interest_calculation_per_year=12
        )
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=account_type,
            account_no=1000000020,
            gender=MALE,
            balance=Decimal('500.00')
        )
    
    def test_deposit_form_valid_amount(self):
        form = DepositForm(
            data={'amount': Decimal('50.00')},
            initial={'transaction_type': DEPOSIT},
            account=self.account
        )
        self.assertTrue(form.is_valid())
    
    def test_deposit_form_rejects_below_minimum(self):
        form = DepositForm(
            data={'amount': Decimal('5.00')},
            initial={'transaction_type': DEPOSIT},
            account=self.account
        )
        self.assertFalse(form.is_valid())
        self.assertIn('amount', form.errors)


class WithdrawFormTests(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='withdraw@example.com',
            password='testpass123'
        )
        self.account_type = BankAccountType.objects.create(
            name='Checking',
            maximum_withdrawal_amount=Decimal('1000.00'),
            annual_interest_rate=Decimal('3.00'),
            interest_calculation_per_year=12
        )
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000030,
            gender=MALE,
            balance=Decimal('500.00')
        )
    
    def test_withdraw_form_valid_amount(self):
        form = WithdrawForm(
            data={'amount': Decimal('100.00')},
            initial={'transaction_type': WITHDRAWAL},
            account=self.account
        )
        self.assertTrue(form.is_valid())
    
    def test_withdraw_form_rejects_below_minimum(self):
        form = WithdrawForm(
            data={'amount': Decimal('5.00')},
            initial={'transaction_type': WITHDRAWAL},
            account=self.account
        )
        self.assertFalse(form.is_valid())
        self.assertIn('amount', form.errors)
    
    def test_withdraw_form_rejects_above_maximum(self):
        form = WithdrawForm(
            data={'amount': Decimal('1500.00')},
            initial={'transaction_type': WITHDRAWAL},
            account=self.account
        )
        self.assertFalse(form.is_valid())
        self.assertIn('amount', form.errors)
    
    def test_withdraw_form_allows_negative_balance_bug(self):
        form = WithdrawForm(
            data={'amount': Decimal('600.00')},
            initial={'transaction_type': WITHDRAWAL},
            account=self.account
        )
        self.assertTrue(form.is_valid(), 
                       "Bug: Form allows withdrawal exceeding balance") # (important-comment)


class DepositMoneyViewTests(TestCase):
    
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            email='depositview@example.com',
            password='testpass123'
        )
        account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('5.00'),
            interest_calculation_per_year=12
        )
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=account_type,
            account_no=1000000040,
            gender=MALE,
            balance=Decimal('100.00')
        )
    
    def test_deposit_updates_balance(self):
        initial_balance = self.account.balance
        request = self.factory.post('/deposit/', {'amount': Decimal('200.00')})
        request.user = self.user
        setattr(request, 'session', {})
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        
        view = DepositMoneyView()
        view.request = request
        form = DepositForm(
            data=request.POST,
            initial={'transaction_type': DEPOSIT},
            account=self.account
        )
        self.assertTrue(form.is_valid())
        
        view.form_valid(form)
        
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, initial_balance + Decimal('200.00'))
    
    def test_first_deposit_sets_dates(self):
        new_user = User.objects.create_user(
            email='newdeposit@example.com',
            password='testpass123'
        )
        account_type = BankAccountType.objects.create(
            name='NewSavings',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('5.00'),
            interest_calculation_per_year=12
        )
        new_account = UserBankAccount.objects.create(
            user=new_user,
            account_type=account_type,
            account_no=1000000041,
            gender=MALE,
            balance=Decimal('0.00'),
            initial_deposit_date=None
        )
        
        request = self.factory.post('/deposit/', {'amount': Decimal('100.00')})
        request.user = new_user
        setattr(request, 'session', {})
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        
        view = DepositMoneyView()
        view.request = request
        form = DepositForm(
            data=request.POST,
            initial={'transaction_type': DEPOSIT},
            account=new_account
        )
        self.assertTrue(form.is_valid())
        
        view.form_valid(form)
        
        new_account.refresh_from_db()
        self.assertIsNotNone(new_account.initial_deposit_date)
        self.assertIsNotNone(new_account.interest_start_date)


class WithdrawMoneyViewTests(TestCase):
    
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            email='withdrawview@example.com',
            password='testpass123'
        )
        account_type = BankAccountType.objects.create(
            name='Checking',
            maximum_withdrawal_amount=Decimal('1000.00'),
            annual_interest_rate=Decimal('3.00'),
            interest_calculation_per_year=12
        )
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=account_type,
            account_no=1000000050,
            gender=MALE,
            balance=Decimal('500.00')
        )
    
    def test_withdraw_updates_balance(self):
        initial_balance = self.account.balance
        request = self.factory.post('/withdraw/', {'amount': Decimal('100.00')})
        request.user = self.user
        setattr(request, 'session', {})
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        
        view = WithdrawMoneyView()
        view.request = request
        form = WithdrawForm(
            data=request.POST,
            initial={'transaction_type': WITHDRAWAL},
            account=self.account
        )
        self.assertTrue(form.is_valid())
        
        view.form_valid(form)
        
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, initial_balance - Decimal('100.00'))
    
    def test_withdraw_allows_negative_balance_bug(self):
        request = self.factory.post('/withdraw/', {'amount': Decimal('600.00')})
        request.user = self.user
        setattr(request, 'session', {})
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        
        view = WithdrawMoneyView()
        view.request = request
        form = WithdrawForm(
            data=request.POST,
            initial={'transaction_type': WITHDRAWAL},
            account=self.account
        )
        
        self.assertTrue(form.is_valid(), "Bug: Form allows over-withdrawal") # (important-comment)
        
        view.form_valid(form)
        
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal('-100.00'),
                        "Bug: Account balance becomes negative") # (important-comment)
