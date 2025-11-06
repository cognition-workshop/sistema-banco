from decimal import Decimal
from datetime import date, datetime, timezone as dt_timezone
from unittest.mock import patch
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from accounts.models import BankAccountType, UserBankAccount
from transactions.models import Transaction
from transactions.forms import (
    DepositForm,
    WithdrawForm,
    TransactionDateRangeForm
)
from transactions.constants import DEPOSIT, WITHDRAWAL, INTEREST
from transactions.tasks import calculate_interest


User = get_user_model()


class TestTransactionModel(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email='trans@example.com',
            password='testpass123'
        )
        self.account_type = BankAccountType.objects.create(
            name='Test Account',
            maximum_withdrawal_amount=5000,
            annual_interest_rate=5,
            interest_calculation_per_year=12
        )
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender='M',
            balance=Decimal('1000.00')
        )

    def test_transaction_creation(self):
        transaction = Transaction.objects.create(
            account=self.account,
            amount=Decimal('100.00'),
            balance_after_transaction=Decimal('1100.00'),
            transaction_type=DEPOSIT
        )
        self.assertEqual(transaction.amount, Decimal('100.00'))
        self.assertEqual(transaction.transaction_type, DEPOSIT)
        self.assertEqual(transaction.account, self.account)

    def test_transaction_string_representation(self):
        transaction = Transaction.objects.create(
            account=self.account,
            amount=Decimal('50.00'),
            balance_after_transaction=Decimal('950.00'),
            transaction_type=WITHDRAWAL
        )
        self.assertEqual(str(transaction), '1000000001')

    def test_transaction_ordering(self):
        trans1 = Transaction.objects.create(
            account=self.account,
            amount=Decimal('100.00'),
            balance_after_transaction=Decimal('1100.00'),
            transaction_type=DEPOSIT
        )
        trans2 = Transaction.objects.create(
            account=self.account,
            amount=Decimal('50.00'),
            balance_after_transaction=Decimal('1150.00'),
            transaction_type=DEPOSIT
        )
        transactions = Transaction.objects.all()
        self.assertEqual(transactions[0], trans1)
        self.assertEqual(transactions[1], trans2)

    def test_transaction_account_relationship(self):
        transaction = Transaction.objects.create(
            account=self.account,
            amount=Decimal('200.00'),
            balance_after_transaction=Decimal('1200.00'),
            transaction_type=DEPOSIT
        )
        self.assertIn(transaction, self.account.transactions.all())


class TestDepositForm(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email='deposit@example.com',
            password='testpass123'
        )
        self.account_type = BankAccountType.objects.create(
            name='Test Account',
            maximum_withdrawal_amount=5000,
            annual_interest_rate=5,
            interest_calculation_per_year=12
        )
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender='M',
            balance=Decimal('500.00')
        )

    def test_valid_deposit_form(self):
        form_data = {
            'amount': Decimal('100.00')
        }
        form = DepositForm(
            data=form_data,
            initial={'transaction_type': DEPOSIT},
            account=self.account
        )
        self.assertTrue(form.is_valid())

    def test_deposit_form_minimum_amount(self):
        form_data = {
            'amount': Decimal(str(settings.MINIMUM_DEPOSIT_AMOUNT))
        }
        form = DepositForm(
            data=form_data,
            initial={'transaction_type': DEPOSIT},
            account=self.account
        )
        self.assertTrue(form.is_valid())

    def test_deposit_form_below_minimum(self):
        form_data = {
            'amount': Decimal('5.00'),
            'transaction_type': DEPOSIT
        }
        form = DepositForm(data=form_data, account=self.account)
        self.assertFalse(form.is_valid())
        self.assertIn('amount', form.errors)

    def test_deposit_form_save(self):
        form_data = {
            'amount': Decimal('250.00')
        }
        form = DepositForm(
            data=form_data,
            initial={'transaction_type': DEPOSIT},
            account=self.account
        )
        self.assertTrue(form.is_valid())
        transaction = form.save()

        self.assertEqual(transaction.amount, Decimal('250.00'))
        self.assertEqual(transaction.account, self.account)
        self.assertEqual(transaction.balance_after_transaction, Decimal('500.00'))


class TestWithdrawForm(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email='withdraw@example.com',
            password='testpass123'
        )
        self.account_type = BankAccountType.objects.create(
            name='Test Account',
            maximum_withdrawal_amount=Decimal('1000.00'),
            annual_interest_rate=5,
            interest_calculation_per_year=12
        )
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender='M',
            balance=Decimal('2000.00')
        )

    def test_valid_withdraw_form(self):
        form_data = {
            'amount': Decimal('500.00')
        }
        form = WithdrawForm(
            data=form_data,
            initial={'transaction_type': WITHDRAWAL},
            account=self.account
        )
        self.assertTrue(form.is_valid())

    def test_withdraw_form_minimum_amount(self):
        form_data = {
            'amount': Decimal(str(settings.MINIMUM_WITHDRAWAL_AMOUNT))
        }
        form = WithdrawForm(
            data=form_data,
            initial={'transaction_type': WITHDRAWAL},
            account=self.account
        )
        self.assertTrue(form.is_valid())

    def test_withdraw_form_below_minimum(self):
        form_data = {
            'amount': Decimal('5.00'),
            'transaction_type': WITHDRAWAL
        }
        form = WithdrawForm(data=form_data, account=self.account)
        self.assertFalse(form.is_valid())
        self.assertIn('amount', form.errors)

    def test_withdraw_form_maximum_amount(self):
        form_data = {
            'amount': self.account_type.maximum_withdrawal_amount
        }
        form = WithdrawForm(
            data=form_data,
            initial={'transaction_type': WITHDRAWAL},
            account=self.account
        )
        self.assertTrue(form.is_valid())

    def test_withdraw_form_above_maximum(self):
        form_data = {
            'amount': Decimal('1500.00'),
            'transaction_type': WITHDRAWAL
        }
        form = WithdrawForm(data=form_data, account=self.account)
        self.assertFalse(form.is_valid())
        self.assertIn('amount', form.errors)

    def test_withdraw_form_prevents_overdraft(self):
        form_data = {
            'amount': Decimal('999.00')
        }
        self.account.balance = Decimal('500.00')
        self.account.save()
        
        form = WithdrawForm(
            data=form_data,
            initial={'transaction_type': WITHDRAWAL},
            account=self.account
        )
        self.assertFalse(form.is_valid())
        self.assertIn('amount', form.errors)


class TestTransactionDateRangeForm(TestCase):

    def test_valid_date_range(self):
        form_data = {
            'daterange': '2024-01-01 - 2024-01-31'
        }
        form = TransactionDateRangeForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['daterange'], ['2024-01-01', '2024-01-31'])

    def test_empty_date_range(self):
        form_data = {
            'daterange': ''
        }
        form = TransactionDateRangeForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_date_format(self):
        form_data = {
            'daterange': '01/01/2024 - 31/01/2024'
        }
        form = TransactionDateRangeForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('daterange', form.errors)

    def test_single_date_invalid(self):
        form_data = {
            'daterange': '2024-01-01'
        }
        form = TransactionDateRangeForm(data=form_data)
        self.assertFalse(form.is_valid())


class TestDepositMoneyView(TestCase):

    def setUp(self):
        self.client = Client()
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=5000,
            annual_interest_rate=6,
            interest_calculation_per_year=4
        )
        self.demo_user = User.objects.create_user(
            email='demo@example.com',
            password='demopass123'
        )
        self.account = UserBankAccount.objects.create(
            user=self.demo_user,
            account_type=self.account_type,
            account_no=1000000001,
            gender='M',
            balance=Decimal('0.00')
        )
        self.url = reverse('transactions:deposit_money')

    def test_deposit_increases_balance(self):
        initial_balance = self.account.balance
        form_data = {
            'amount': Decimal('500.00')
        }
        response = self.client.post(self.url, data=form_data)

        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, initial_balance + Decimal('500.00'))

    @patch('transactions.views.timezone.now')
    def test_first_deposit_sets_dates(self, mock_now):
        mock_date = datetime(2024, 1, 15, 12, 0, 0, tzinfo=dt_timezone.utc)
        mock_now.return_value = mock_date

        self.account.initial_deposit_date = None
        self.account.interest_start_date = None
        self.account.save()

        form_data = {
            'amount': Decimal('1000.00')
        }
        self.client.post(self.url, data=form_data)

        self.account.refresh_from_db()
        self.assertIsNotNone(self.account.initial_deposit_date)
        self.assertIsNotNone(self.account.interest_start_date)
        self.assertEqual(self.account.initial_deposit_date, mock_date.date())

    def test_deposit_creates_transaction(self):
        form_data = {
            'amount': Decimal('750.00')
        }
        self.client.post(self.url, data=form_data)

        transaction = Transaction.objects.filter(
            account=self.account,
            transaction_type=DEPOSIT
        ).first()
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction.amount, Decimal('750.00'))


class TestWithdrawMoneyView(TestCase):

    def setUp(self):
        self.client = Client()
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=2000,
            annual_interest_rate=5,
            interest_calculation_per_year=12
        )
        self.demo_user = User.objects.create_user(
            email='demo@example.com',
            password='demopass123'
        )
        self.account = UserBankAccount.objects.create(
            user=self.demo_user,
            account_type=self.account_type,
            account_no=1000000001,
            gender='F',
            balance=Decimal('3000.00')
        )
        self.url = reverse('transactions:withdraw_money')

    def test_withdrawal_decreases_balance(self):
        initial_balance = self.account.balance
        form_data = {
            'amount': Decimal('500.00')
        }
        response = self.client.post(self.url, data=form_data)

        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, initial_balance - Decimal('500.00'))

    def test_withdrawal_creates_transaction(self):
        form_data = {
            'amount': Decimal('800.00')
        }
        self.client.post(self.url, data=form_data)

        transaction = Transaction.objects.filter(
            account=self.account,
            transaction_type=WITHDRAWAL
        ).first()
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction.amount, Decimal('800.00'))


class TestTransactionReportView(TestCase):

    def setUp(self):
        self.client = Client()
        self.account_type = BankAccountType.objects.create(
            name='Test Account',
            maximum_withdrawal_amount=5000,
            annual_interest_rate=5,
            interest_calculation_per_year=12
        )
        self.demo_user = User.objects.create_user(
            email='demo@example.com',
            password='demopass123'
        )
        self.account = UserBankAccount.objects.create(
            user=self.demo_user,
            account_type=self.account_type,
            account_no=1000000001,
            gender='M',
            balance=Decimal('1000.00')
        )
        self.trans1 = Transaction.objects.create(
            account=self.account,
            amount=Decimal('500.00'),
            balance_after_transaction=Decimal('500.00'),
            transaction_type=DEPOSIT
        )
        self.trans2 = Transaction.objects.create(
            account=self.account,
            amount=Decimal('200.00'),
            balance_after_transaction=Decimal('700.00'),
            transaction_type=DEPOSIT
        )
        self.url = reverse('transactions:transaction_report')

    def test_view_returns_all_transactions(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('object_list', response.context)


class TestCalculateInterestTask(TestCase):

    def setUp(self):
        self.account_type = BankAccountType.objects.create(
            name='Interest Account',
            maximum_withdrawal_amount=5000,
            annual_interest_rate=12,
            interest_calculation_per_year=12
        )
        self.user = User.objects.create_user(
            email='interest@example.com',
            password='testpass123'
        )

    @patch('transactions.tasks.timezone.now')
    def test_calculate_interest_for_eligible_account(self, mock_now):
        mock_date = datetime(2024, 3, 1, tzinfo=dt_timezone.utc)
        mock_now.return_value = mock_date

        account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender='M',
            balance=Decimal('1000.00'),
            initial_deposit_date=date(2024, 1, 1),
            interest_start_date=date(2024, 1, 1)
        )

        calculate_interest()

        account.refresh_from_db()
        self.assertEqual(account.balance, Decimal('1010.00'))

        interest_transaction = Transaction.objects.filter(
            account=account,
            transaction_type=INTEREST
        ).first()
        self.assertIsNotNone(interest_transaction)
        self.assertEqual(interest_transaction.amount, Decimal('10.00'))

    def test_no_interest_for_zero_balance(self):
        account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000002,
            gender='F',
            balance=Decimal('0.00'),
            initial_deposit_date=date(2024, 1, 1),
            interest_start_date=date(2024, 1, 1)
        )

        calculate_interest()

        account.refresh_from_db()
        self.assertEqual(account.balance, Decimal('0.00'))

    def test_no_interest_before_start_date(self):
        future_date = timezone.now() + timezone.timedelta(days=365)
        account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000003,
            gender='M',
            balance=Decimal('1000.00'),
            initial_deposit_date=date(2024, 1, 1),
            interest_start_date=future_date.date()
        )

        calculate_interest()

        account.refresh_from_db()
        self.assertEqual(account.balance, Decimal('1000.00'))


from .serializers import TransactionSerializer
from accounts.models import UserBankAccount, BankAccountType
from accounts.constants import MALE

User = get_user_model()


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
        """Test that all fields are read-only and ignored during deserialization"""
        data = {
            'amount': '200.00',
            'balance_after_transaction': '1200.00',
            'transaction_type': WITHDRAWAL
        }
        
        serializer = TransactionSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data, {})


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
