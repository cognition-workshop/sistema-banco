from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from datetime import date, datetime

from .models import Transaction
from .forms import TransactionForm, DepositForm, WithdrawForm, TransactionDateRangeForm
from .constants import DEPOSIT, WITHDRAWAL, INTEREST
from accounts.models import BankAccountType, UserBankAccount
from accounts.constants import MALE


User = get_user_model()


class TransactionModelTestCase(TestCase):
    
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
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender=MALE,
            balance=Decimal('1000.00')
        )
        
    def test_transaction_creation(self):
        transaction = Transaction.objects.create(
            account=self.account,
            amount=Decimal('100.00'),
            balance_after_transaction=Decimal('1100.00'),
            transaction_type=DEPOSIT
        )
        self.assertEqual(transaction.account, self.account)
        self.assertEqual(transaction.amount, Decimal('100.00'))
        self.assertEqual(transaction.transaction_type, DEPOSIT)
        
    def test_balance_after_transaction_recording(self):
        transaction = Transaction.objects.create(
            account=self.account,
            amount=Decimal('100.00'),
            balance_after_transaction=Decimal('1100.00'),
            transaction_type=DEPOSIT
        )
        self.assertEqual(transaction.balance_after_transaction, Decimal('1100.00'))
        
    def test_transaction_type_choices(self):
        deposit = Transaction.objects.create(
            account=self.account,
            amount=Decimal('100.00'),
            balance_after_transaction=Decimal('1100.00'),
            transaction_type=DEPOSIT
        )
        withdrawal = Transaction.objects.create(
            account=self.account,
            amount=Decimal('50.00'),
            balance_after_transaction=Decimal('1050.00'),
            transaction_type=WITHDRAWAL
        )
        interest = Transaction.objects.create(
            account=self.account,
            amount=Decimal('10.00'),
            balance_after_transaction=Decimal('1060.00'),
            transaction_type=INTEREST
        )
        self.assertEqual(deposit.transaction_type, DEPOSIT)
        self.assertEqual(withdrawal.transaction_type, WITHDRAWAL)
        self.assertEqual(interest.transaction_type, INTEREST)
        
    def test_transaction_ordering_by_timestamp(self):
        trans1 = Transaction.objects.create(
            account=self.account,
            amount=Decimal('100.00'),
            balance_after_transaction=Decimal('1100.00'),
            transaction_type=DEPOSIT
        )
        trans2 = Transaction.objects.create(
            account=self.account,
            amount=Decimal('50.00'),
            balance_after_transaction=Decimal('1050.00'),
            transaction_type=WITHDRAWAL
        )
        transactions = Transaction.objects.all()
        self.assertEqual(transactions[0], trans1)
        self.assertEqual(transactions[1], trans2)
        
    def test_string_representation(self):
        transaction = Transaction.objects.create(
            account=self.account,
            amount=Decimal('100.00'),
            balance_after_transaction=Decimal('1100.00'),
            transaction_type=DEPOSIT
        )
        self.assertEqual(str(transaction), '1000000001')


class TransactionFormTestCase(TestCase):
    
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
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender=MALE,
            balance=Decimal('1000.00')
        )
        
    def test_form_initialization_with_account(self):
        form = TransactionForm(account=self.account)
        self.assertEqual(form.account, self.account)
        
    def test_transaction_type_field_disabled(self):
        form = TransactionForm(account=self.account)
        self.assertTrue(form.fields['transaction_type'].disabled)
        
    def test_save_method_sets_account_and_balance(self):
        form_data = {
            'amount': Decimal('100.00')
        }
        form = TransactionForm(data=form_data, account=self.account, initial={'transaction_type': DEPOSIT})
        self.assertTrue(form.is_valid())
        transaction = form.save()
        self.assertEqual(transaction.account, self.account)
        self.assertEqual(transaction.balance_after_transaction, self.account.balance)


class DepositFormTestCase(TestCase):
    
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
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender=MALE,
            balance=Decimal('1000.00')
        )
        
    def test_minimum_deposit_amount_validation(self):
        form_data = {
            'amount': Decimal('5.00')
        }
        form = DepositForm(data=form_data, account=self.account, initial={'transaction_type': DEPOSIT})
        self.assertFalse(form.is_valid())
        self.assertIn('amount', form.errors)
        
    def test_valid_deposit_amount(self):
        form_data = {
            'amount': Decimal('100.00')
        }
        form = DepositForm(data=form_data, account=self.account, initial={'transaction_type': DEPOSIT})
        self.assertTrue(form.is_valid())
        
    def test_deposit_at_minimum_boundary(self):
        form_data = {
            'amount': Decimal('10.00')
        }
        form = DepositForm(data=form_data, account=self.account, initial={'transaction_type': DEPOSIT})
        self.assertTrue(form.is_valid())
        
    def test_clean_amount_method(self):
        form_data = {
            'amount': Decimal('100.00')
        }
        form = DepositForm(data=form_data, account=self.account, initial={'transaction_type': DEPOSIT})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['amount'], Decimal('100.00'))


class WithdrawFormTestCase(TestCase):
    
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
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender=MALE,
            balance=Decimal('1000.00')
        )
        
    def test_minimum_withdrawal_amount_validation(self):
        form_data = {
            'amount': Decimal('5.00')
        }
        form = WithdrawForm(data=form_data, account=self.account, initial={'transaction_type': WITHDRAWAL})
        self.assertFalse(form.is_valid())
        self.assertIn('amount', form.errors)
        
    def test_maximum_withdrawal_amount_validation(self):
        form_data = {
            'amount': Decimal('6000.00')
        }
        form = WithdrawForm(data=form_data, account=self.account, initial={'transaction_type': WITHDRAWAL})
        self.assertFalse(form.is_valid())
        self.assertIn('amount', form.errors)
        
    def test_withdraw_form_prevents_overdraft(self):
        form_data = {
            'amount': Decimal('1500.00')
        }
        form = WithdrawForm(data=form_data, account=self.account, initial={'transaction_type': WITHDRAWAL})
        self.assertFalse(form.is_valid())
        self.assertIn('amount', form.errors)
        self.assertIn('insufficient balance', str(form.errors['amount']).lower())
        
    def test_valid_withdrawal_amount(self):
        form_data = {
            'amount': Decimal('500.00')
        }
        form = WithdrawForm(data=form_data, account=self.account, initial={'transaction_type': WITHDRAWAL})
        self.assertTrue(form.is_valid())
        
    def test_withdrawal_at_exact_balance(self):
        form_data = {
            'amount': Decimal('1000.00')
        }
        form = WithdrawForm(data=form_data, account=self.account, initial={'transaction_type': WITHDRAWAL})
        self.assertTrue(form.is_valid())


class TransactionDateRangeFormTestCase(TestCase):
    
    def test_valid_date_range(self):
        form_data = {
            'daterange': '2023-01-01 - 2023-12-31'
        }
        form = TransactionDateRangeForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['daterange'], ['2023-01-01', '2023-12-31'])
        
    def test_invalid_date_format(self):
        form_data = {
            'daterange': 'invalid-date-range'
        }
        form = TransactionDateRangeForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('daterange', form.errors)
        
    def test_single_date_invalid(self):
        form_data = {
            'daterange': '2023-01-01'
        }
        form = TransactionDateRangeForm(data=form_data)
        self.assertFalse(form.is_valid())
        
    def test_empty_daterange(self):
        form_data = {
            'daterange': ''
        }
        form = TransactionDateRangeForm(data=form_data)
        self.assertFalse(form.is_valid())


class DepositMoneyViewTestCase(TestCase):
    
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
            password='testpass123'
        )
        self.account = UserBankAccount.objects.create(
            user=self.demo_user,
            account_type=self.account_type,
            account_no=1000000001,
            gender=MALE,
            balance=Decimal('0.00')
        )
        
    def test_get_request_returns_form(self):
        response = self.client.get(reverse('transactions:deposit_money'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        
    def test_post_with_valid_amount_updates_balance(self):
        initial_balance = self.account.balance
        form_data = {
            'amount': Decimal('100.00'),
            'transaction_type': DEPOSIT
        }
        response = self.client.post(reverse('transactions:deposit_money'), data=form_data)
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, initial_balance + Decimal('100.00'))
        
    def test_first_deposit_sets_dates(self):
        self.assertIsNone(self.account.initial_deposit_date)
        self.assertIsNone(self.account.interest_start_date)
        
        form_data = {
            'amount': Decimal('100.00'),
            'transaction_type': DEPOSIT
        }
        response = self.client.post(reverse('transactions:deposit_money'), data=form_data)
        self.account.refresh_from_db()
        
        self.assertIsNotNone(self.account.initial_deposit_date)
        self.assertIsNotNone(self.account.interest_start_date)
        
    def test_deposit_below_minimum_rejected(self):
        form_data = {
            'amount': Decimal('5.00'),
            'transaction_type': DEPOSIT
        }
        response = self.client.post(reverse('transactions:deposit_money'), data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'amount', None)
        
    def test_successful_deposit_message(self):
        form_data = {
            'amount': Decimal('100.00'),
            'transaction_type': DEPOSIT
        }
        response = self.client.post(reverse('transactions:deposit_money'), data=form_data, follow=True)
        messages = list(response.context['messages'])
        self.assertTrue(any('deposited' in str(m).lower() for m in messages))


class WithdrawMoneyViewTestCase(TestCase):
    
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
            password='testpass123'
        )
        self.account = UserBankAccount.objects.create(
            user=self.demo_user,
            account_type=self.account_type,
            account_no=1000000001,
            gender=MALE,
            balance=Decimal('1000.00')
        )
        
    def test_get_request_returns_form(self):
        response = self.client.get(reverse('transactions:withdraw_money'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        
    def test_post_with_valid_amount_updates_balance(self):
        initial_balance = self.account.balance
        form_data = {
            'amount': Decimal('100.00'),
            'transaction_type': WITHDRAWAL
        }
        response = self.client.post(reverse('transactions:withdraw_money'), data=form_data)
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, initial_balance - Decimal('100.00'))
        
    def test_withdrawal_below_minimum_rejected(self):
        form_data = {
            'amount': Decimal('5.00'),
            'transaction_type': WITHDRAWAL
        }
        response = self.client.post(reverse('transactions:withdraw_money'), data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'amount', None)
        
    def test_withdrawal_above_maximum_rejected(self):
        form_data = {
            'amount': Decimal('6000.00'),
            'transaction_type': WITHDRAWAL
        }
        response = self.client.post(reverse('transactions:withdraw_money'), data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'amount', None)
        
    def test_withdrawal_above_balance_rejected(self):
        form_data = {
            'amount': Decimal('1500.00'),
            'transaction_type': WITHDRAWAL
        }
        response = self.client.post(reverse('transactions:withdraw_money'), data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'amount', None)
        
    def test_successful_withdrawal_message(self):
        form_data = {
            'amount': Decimal('100.00'),
            'transaction_type': WITHDRAWAL
        }
        response = self.client.post(reverse('transactions:withdraw_money'), data=form_data, follow=True)
        messages = list(response.context['messages'])
        self.assertTrue(any('withdrawn' in str(m).lower() for m in messages))


class TransactionRepostViewTestCase(TestCase):
    
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
            password='testpass123'
        )
        self.account = UserBankAccount.objects.create(
            user=self.demo_user,
            account_type=self.account_type,
            account_no=1000000001,
            gender=MALE,
            balance=Decimal('1000.00')
        )
        
    def test_get_request_returns_transaction_list(self):
        Transaction.objects.create(
            account=self.account,
            amount=Decimal('100.00'),
            balance_after_transaction=Decimal('1100.00'),
            transaction_type=DEPOSIT
        )
        response = self.client.get(reverse('transactions:transaction_report'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('object_list', response.context)
        
    def test_queryset_filtered_by_demo_account(self):
        other_user = User.objects.create_user(
            email='other@example.com',
            password='testpass123'
        )
        other_account = UserBankAccount.objects.create(
            user=other_user,
            account_type=self.account_type,
            account_no=1000000002,
            gender=MALE,
            balance=Decimal('500.00')
        )
        
        Transaction.objects.create(
            account=self.account,
            amount=Decimal('100.00'),
            balance_after_transaction=Decimal('1100.00'),
            transaction_type=DEPOSIT
        )
        Transaction.objects.create(
            account=other_account,
            amount=Decimal('50.00'),
            balance_after_transaction=Decimal('550.00'),
            transaction_type=DEPOSIT
        )
        
        response = self.client.get(reverse('transactions:transaction_report'))
        transactions = response.context['object_list']
        self.assertEqual(transactions.count(), 1)
        self.assertEqual(transactions[0].account, self.account)
        
    def test_context_includes_account_and_form(self):
        response = self.client.get(reverse('transactions:transaction_report'))
        self.assertIn('account', response.context)
        self.assertIn('form', response.context)
        self.assertEqual(response.context['account'], self.account)
