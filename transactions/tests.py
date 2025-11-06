from decimal import Decimal
from django.test import TestCase, TransactionTestCase, Client
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.urls import reverse

from accounts.models import UserBankAccount, BankAccountType
from transactions.models import Transaction
from transactions.constants import DEPOSIT, WITHDRAWAL, INTEREST

User = get_user_model()


class TransactionImmutabilityTests(TestCase):
    """Test that transactions cannot be modified or deleted."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('10000.00'),
            annual_interest_rate=Decimal('5.00'),
            interest_calculation_per_year=12
        )
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender='M',
            balance=Decimal('1000.00')
        )
    
    def test_cannot_update_transaction(self):
        """Test that updating a transaction raises ValidationError."""
        transaction = Transaction.objects.create(
            account=self.account,
            amount=Decimal('100.00'),
            previous_balance=Decimal('1000.00'),
            balance_after_transaction=Decimal('1100.00'),
            transaction_type=DEPOSIT,
            user=self.user
        )
        
        transaction.amount = Decimal('200.00')
        with self.assertRaises(ValidationError):
            transaction.save()
    
    def test_cannot_delete_transaction(self):
        """Test that deleting a transaction only marks it as deleted."""
        transaction = Transaction.objects.create(
            account=self.account,
            amount=Decimal('100.00'),
            previous_balance=Decimal('1000.00'),
            balance_after_transaction=Decimal('1100.00'),
            transaction_type=DEPOSIT,
            user=self.user
        )
        
        transaction.delete()
        
        self.assertTrue(Transaction.objects.filter(pk=transaction.pk).exists())
        
        transaction.refresh_from_db()
        self.assertTrue(transaction.is_deleted)
    
    def test_transaction_uses_protect_on_delete(self):
        """Test that CASCADE is prevented on account deletion."""
        transaction = Transaction.objects.create(
            account=self.account,
            amount=Decimal('100.00'),
            previous_balance=Decimal('1000.00'),
            balance_after_transaction=Decimal('1100.00'),
            transaction_type=DEPOSIT,
            user=self.user
        )
        
        from django.db.models import ProtectedError
        with self.assertRaises(ProtectedError):
            self.account.delete()


class HashIntegrityTests(TestCase):
    """Test hash calculation and chain integrity."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('10000.00'),
            annual_interest_rate=Decimal('5.00'),
            interest_calculation_per_year=12
        )
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender='M',
            balance=Decimal('1000.00')
        )
    
    def test_hash_automatically_calculated(self):
        """Test that hash is calculated automatically on save."""
        transaction = Transaction.objects.create(
            account=self.account,
            amount=Decimal('100.00'),
            previous_balance=Decimal('1000.00'),
            balance_after_transaction=Decimal('1100.00'),
            transaction_type=DEPOSIT,
            user=self.user
        )
        
        self.assertIsNotNone(transaction.current_hash)
        self.assertEqual(len(transaction.current_hash), 64)
    
    def test_hash_integrity_verification(self):
        """Test that hash integrity can be verified."""
        transaction = Transaction.objects.create(
            account=self.account,
            amount=Decimal('100.00'),
            previous_balance=Decimal('1000.00'),
            balance_after_transaction=Decimal('1100.00'),
            transaction_type=DEPOSIT,
            user=self.user
        )
        
        self.assertTrue(transaction.verify_hash_integrity())
    
    def test_hash_chain_integrity(self):
        """Test that hash chain links transactions correctly."""
        tx1 = Transaction.objects.create(
            account=self.account,
            amount=Decimal('100.00'),
            previous_balance=Decimal('1000.00'),
            balance_after_transaction=Decimal('1100.00'),
            transaction_type=DEPOSIT,
            user=self.user
        )
        
        tx2 = Transaction.objects.create(
            account=self.account,
            amount=Decimal('50.00'),
            previous_balance=Decimal('1100.00'),
            balance_after_transaction=Decimal('1150.00'),
            transaction_type=DEPOSIT,
            user=self.user
        )
        
        self.assertEqual(tx2.previous_hash, tx1.current_hash)
        self.assertTrue(tx2.verify_chain_integrity())
    
    def test_first_transaction_has_no_previous_hash(self):
        """Test that first transaction has null previous_hash."""
        transaction = Transaction.objects.create(
            account=self.account,
            amount=Decimal('100.00'),
            previous_balance=Decimal('1000.00'),
            balance_after_transaction=Decimal('1100.00'),
            transaction_type=DEPOSIT,
            user=self.user
        )
        
        self.assertIsNone(transaction.previous_hash)
        self.assertTrue(transaction.verify_chain_integrity())


class AuditCaptureTests(TestCase):
    """Test that user and IP information is captured."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('10000.00'),
            annual_interest_rate=Decimal('5.00'),
            interest_calculation_per_year=12
        )
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender='M',
            balance=Decimal('1000.00')
        )
    
    def test_transaction_captures_user_and_metadata(self):
        """Test that transactions capture user and metadata."""
        transaction = Transaction.objects.create(
            account=self.account,
            amount=Decimal('100.00'),
            previous_balance=Decimal('1000.00'),
            balance_after_transaction=Decimal('1100.00'),
            transaction_type=DEPOSIT,
            user=self.user,
            metadata={'test': 'data'}
        )
        
        self.assertEqual(transaction.user, self.user)
        self.assertEqual(transaction.metadata.get('test'), 'data')
    
    def test_system_transaction_has_null_user(self):
        """Test that system transactions can have null user."""
        transaction = Transaction.objects.create(
            account=self.account,
            amount=Decimal('5.00'),
            previous_balance=Decimal('1000.00'),
            balance_after_transaction=Decimal('1005.00'),
            transaction_type=INTEREST,
            user=None,
            metadata={'automated': True}
        )
        
        self.assertIsNone(transaction.user)
        self.assertEqual(transaction.transaction_type, INTEREST)


class AuditQueryTests(TestCase):
    """Test audit query functionality."""
    
    def setUp(self):
        self.user1 = User.objects.create_user(
            email='user1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            email='user2@example.com',
            password='testpass123'
        )
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('10000.00'),
            annual_interest_rate=Decimal('5.00'),
            interest_calculation_per_year=12
        )
        self.account1 = UserBankAccount.objects.create(
            user=self.user1,
            account_type=self.account_type,
            account_no=1000000001,
            gender='M',
            balance=Decimal('1000.00')
        )
        self.account2 = UserBankAccount.objects.create(
            user=self.user2,
            account_type=self.account_type,
            account_no=1000000002,
            gender='F',
            balance=Decimal('2000.00')
        )
    
    def test_query_by_user(self):
        """Test querying transactions by user."""
        Transaction.objects.create(
            account=self.account1,
            amount=Decimal('100.00'),
            previous_balance=Decimal('1000.00'),
            balance_after_transaction=Decimal('1100.00'),
            transaction_type=DEPOSIT,
            user=self.user1
        )
        Transaction.objects.create(
            account=self.account2,
            amount=Decimal('200.00'),
            previous_balance=Decimal('2000.00'),
            balance_after_transaction=Decimal('2200.00'),
            transaction_type=DEPOSIT,
            user=self.user2
        )
        
        user1_txs = Transaction.audit.for_user(self.user1)
        self.assertEqual(user1_txs.count(), 1)
        self.assertEqual(user1_txs.first().user, self.user1)
    
    def test_query_by_account(self):
        """Test querying transactions by account."""
        Transaction.objects.create(
            account=self.account1,
            amount=Decimal('100.00'),
            previous_balance=Decimal('1000.00'),
            balance_after_transaction=Decimal('1100.00'),
            transaction_type=DEPOSIT,
            user=self.user1
        )
        Transaction.objects.create(
            account=self.account1,
            amount=Decimal('50.00'),
            previous_balance=Decimal('1100.00'),
            balance_after_transaction=Decimal('1050.00'),
            transaction_type=WITHDRAWAL,
            user=self.user1
        )
        
        account_txs = Transaction.audit.for_account(self.account1)
        self.assertEqual(account_txs.count(), 2)
    
    def test_query_by_type(self):
        """Test querying transactions by type."""
        Transaction.objects.create(
            account=self.account1,
            amount=Decimal('100.00'),
            previous_balance=Decimal('1000.00'),
            balance_after_transaction=Decimal('1100.00'),
            transaction_type=DEPOSIT,
            user=self.user1
        )
        Transaction.objects.create(
            account=self.account1,
            amount=Decimal('50.00'),
            previous_balance=Decimal('1100.00'),
            balance_after_transaction=Decimal('1050.00'),
            transaction_type=WITHDRAWAL,
            user=self.user1
        )
        
        deposits = Transaction.audit.by_type(DEPOSIT)
        self.assertEqual(deposits.count(), 1)
        self.assertEqual(deposits.first().transaction_type, DEPOSIT)
    
    def test_query_by_date_range(self):
        """Test querying transactions by date range."""
        from datetime import date, timedelta
        
        today = date.today()
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)
        
        Transaction.objects.create(
            account=self.account1,
            amount=Decimal('100.00'),
            previous_balance=Decimal('1000.00'),
            balance_after_transaction=Decimal('1100.00'),
            transaction_type=DEPOSIT,
            user=self.user1
        )
        
        txs = Transaction.audit.by_date_range(yesterday, tomorrow)
        self.assertGreater(txs.count(), 0)
    
    def test_soft_delete_filters_deleted_transactions(self):
        """Test that audit manager filters out deleted transactions."""
        tx = Transaction.objects.create(
            account=self.account1,
            amount=Decimal('100.00'),
            previous_balance=Decimal('1000.00'),
            balance_after_transaction=Decimal('1100.00'),
            transaction_type=DEPOSIT,
            user=self.user1
        )
        
        self.assertEqual(Transaction.audit.count(), 1)
        
        tx.delete()
        
        self.assertEqual(Transaction.audit.count(), 0)
        self.assertEqual(Transaction.objects.count(), 1)


class NegativeBalanceTests(TestCase):
    """Test that negative balance validation works."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('10000.00'),
            annual_interest_rate=Decimal('5.00'),
            interest_calculation_per_year=12
        )
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender='M',
            balance=Decimal('100.00')
        )
    
    def test_cannot_withdraw_more_than_balance(self):
        """Test that withdrawing more than balance is prevented."""
        from transactions.forms import WithdrawForm
        
        form = WithdrawForm(
            data={'amount': Decimal('200.00'), 'transaction_type': WITHDRAWAL},
            account=self.account
        )
        
        self.assertFalse(form.is_valid())
        self.assertIn('Insufficient funds', str(form.errors))


class PreviousBalanceCaptureTests(TestCase):
    """Test that previous balance is captured correctly."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('10000.00'),
            annual_interest_rate=Decimal('5.00'),
            interest_calculation_per_year=12
        )
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender='M',
            balance=Decimal('1000.00')
        )
    
    def test_previous_balance_captured_on_deposit(self):
        """Test that previous balance is captured before deposit."""
        initial_balance = self.account.balance
        
        transaction = Transaction.objects.create(
            account=self.account,
            amount=Decimal('100.00'),
            previous_balance=initial_balance,
            balance_after_transaction=initial_balance + Decimal('100.00'),
            transaction_type=DEPOSIT,
            user=self.user
        )
        
        self.assertEqual(transaction.previous_balance, initial_balance)
        self.assertEqual(
            transaction.balance_after_transaction,
            initial_balance + Decimal('100.00')
        )
    
    def test_previous_balance_captured_on_withdrawal(self):
        """Test that previous balance is captured before withdrawal."""
        initial_balance = self.account.balance
        
        transaction = Transaction.objects.create(
            account=self.account,
            amount=Decimal('100.00'),
            previous_balance=initial_balance,
            balance_after_transaction=initial_balance - Decimal('100.00'),
            transaction_type=WITHDRAWAL,
            user=self.user
        )
        
        self.assertEqual(transaction.previous_balance, initial_balance)
        self.assertEqual(
            transaction.balance_after_transaction,
            initial_balance - Decimal('100.00')
        )
