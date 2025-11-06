from decimal import Decimal
from unittest.mock import Mock, patch
from datetime import datetime, date

from django.test import TestCase
from django.utils import timezone

from transactions.utils import process_interest_for_accounts
from transactions.tasks import calculate_interest
from transactions.constants import INTEREST
from accounts.models import UserBankAccount, BankAccountType, User
from transactions.models import Transaction


class ProcessInterestForAccountsTests(TestCase):
    """Test suite for the pure utility function process_interest_for_accounts."""
    
    def setUp(self):
        """Set up mock objects for testing."""
        self.mock_account_type = Mock()
        self.mock_account_type.calculate_interest.return_value = Decimal('10.50')
        
    def test_empty_accounts_list(self):
        """Test that empty accounts list returns empty results."""
        transactions, updates = process_interest_for_accounts([], 6)
        
        self.assertEqual(transactions, [])
        self.assertEqual(updates, [])
    
    def test_invalid_month_raises_error(self):
        """Test that invalid month values raise ValueError."""
        mock_account = Mock()
        
        with self.assertRaises(ValueError) as context:
            process_interest_for_accounts([mock_account], 0)
        self.assertIn("must be between 1 and 12", str(context.exception))
        
        with self.assertRaises(ValueError) as context:
            process_interest_for_accounts([mock_account], 13)
        self.assertIn("must be between 1 and 12", str(context.exception))
    
    def test_account_not_in_calculation_month(self):
        """Test that accounts not in calculation month are skipped."""
        mock_account = Mock()
        mock_account.balance = Decimal('1000.00')
        mock_account.account_type = self.mock_account_type
        mock_account.get_interest_calculation_months.return_value = [3, 6, 9, 12]
        
        transactions, updates = process_interest_for_accounts([mock_account], 5)
        
        self.assertEqual(len(transactions), 0)
        self.assertEqual(len(updates), 0)
        self.mock_account_type.calculate_interest.assert_not_called()
    
    def test_account_in_calculation_month(self):
        """Test successful interest calculation for eligible account."""
        mock_account = Mock()
        mock_account.balance = Decimal('1000.00')
        mock_account.account_type = self.mock_account_type
        mock_account.get_interest_calculation_months.return_value = [3, 6, 9, 12]
        
        transactions, updates = process_interest_for_accounts([mock_account], 6)
        
        self.assertEqual(len(transactions), 1)
        self.assertEqual(len(updates), 1)
        
        self.assertEqual(transactions[0]['account'], mock_account)
        self.assertEqual(transactions[0]['transaction_type'], INTEREST)
        self.assertEqual(transactions[0]['amount'], Decimal('10.50'))
        self.assertEqual(transactions[0]['balance_after_transaction'], Decimal('1010.50'))
        
        self.assertEqual(updates[0]['account'], mock_account)
        self.assertEqual(updates[0]['new_balance'], Decimal('1010.50'))
        
        self.mock_account_type.calculate_interest.assert_called_once_with(Decimal('1000.00'))
    
    def test_multiple_accounts_mixed_eligibility(self):
        """Test processing multiple accounts with different eligibility."""
        mock_account1 = Mock()
        mock_account1.balance = Decimal('1000.00')
        mock_account1.account_type = self.mock_account_type
        mock_account1.get_interest_calculation_months.return_value = [6, 12]
        
        mock_account2 = Mock()
        mock_account2.balance = Decimal('2000.00')
        mock_account2.account_type = self.mock_account_type
        mock_account2.get_interest_calculation_months.return_value = [3, 9]
        
        mock_account_type3 = Mock()
        mock_account_type3.calculate_interest.return_value = Decimal('25.00')
        mock_account3 = Mock()
        mock_account3.balance = Decimal('5000.00')
        mock_account3.account_type = mock_account_type3
        mock_account3.get_interest_calculation_months.return_value = [1, 6, 12]
        
        transactions, updates = process_interest_for_accounts(
            [mock_account1, mock_account2, mock_account3], 
            6
        )
        
        self.assertEqual(len(transactions), 2)
        self.assertEqual(len(updates), 2)
        
        self.assertEqual(transactions[0]['account'], mock_account1)
        self.assertEqual(transactions[0]['amount'], Decimal('10.50'))
        
        self.assertEqual(transactions[1]['account'], mock_account3)
        self.assertEqual(transactions[1]['amount'], Decimal('25.00'))
    
    def test_zero_balance_with_positive_interest(self):
        """Test account with zero balance getting interest."""
        mock_account = Mock()
        mock_account.balance = Decimal('0.00')
        mock_account.account_type = self.mock_account_type
        mock_account.get_interest_calculation_months.return_value = [6]
        
        transactions, updates = process_interest_for_accounts([mock_account], 6)
        
        self.assertEqual(len(transactions), 1)
        self.assertEqual(transactions[0]['balance_after_transaction'], Decimal('10.50'))
    
    def test_large_balance_calculation(self):
        """Test interest calculation with large balance."""
        mock_account_type = Mock()
        mock_account_type.calculate_interest.return_value = Decimal('1234.56')
        
        mock_account = Mock()
        mock_account.balance = Decimal('100000.00')
        mock_account.account_type = mock_account_type
        mock_account.get_interest_calculation_months.return_value = [6]
        
        transactions, updates = process_interest_for_accounts([mock_account], 6)
        
        self.assertEqual(transactions[0]['amount'], Decimal('1234.56'))
        self.assertEqual(transactions[0]['balance_after_transaction'], Decimal('101234.56'))
    
    def test_all_twelve_months(self):
        """Test that all months 1-12 are valid."""
        mock_account = Mock()
        mock_account.balance = Decimal('1000.00')
        mock_account.account_type = self.mock_account_type
        mock_account.get_interest_calculation_months.return_value = list(range(1, 13))
        
        for month in range(1, 13):
            transactions, updates = process_interest_for_accounts([mock_account], month)
            self.assertEqual(len(transactions), 1, f"Failed for month {month}")
    
    def test_negative_month_raises_error(self):
        """Test that negative month values raise ValueError."""
        mock_account = Mock()
        
        with self.assertRaises(ValueError) as context:
            process_interest_for_accounts([mock_account], -1)
        self.assertIn("must be between 1 and 12", str(context.exception))
    
    def test_decimal_precision_preserved(self):
        """Test that decimal precision is maintained in calculations."""
        mock_account_type = Mock()
        mock_account_type.calculate_interest.return_value = Decimal('0.01')
        
        mock_account = Mock()
        mock_account.balance = Decimal('100.00')
        mock_account.account_type = mock_account_type
        mock_account.get_interest_calculation_months.return_value = [1]
        
        transactions, updates = process_interest_for_accounts([mock_account], 1)
        
        self.assertEqual(transactions[0]['amount'], Decimal('0.01'))
        self.assertEqual(transactions[0]['balance_after_transaction'], Decimal('100.01'))


class CalculateInterestTaskTests(TestCase):
    """Integration tests for the Celery task."""
    
    def setUp(self):
        """Set up test data."""
        self.account_type = BankAccountType.objects.create(
            name='Savings Account',
            maximum_withdrawal_amount=Decimal('10000.00'),
            annual_interest_rate=Decimal('5.00'),
            interest_calculation_per_year=12
        )
    
    @patch('transactions.tasks.timezone')
    def test_calculate_interest_task_integration(self, mock_timezone):
        """Test the full Celery task integration."""
        mock_now = datetime(2024, 6, 15, 12, 0, 0)
        mock_timezone.now.return_value = mock_now
        
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        account = UserBankAccount.objects.create(
            user=user,
            account_type=self.account_type,
            account_no=123456,
            gender='M',
            balance=Decimal('1000.00'),
            interest_start_date=date(2024, 1, 1),
            initial_deposit_date=date(2024, 1, 1)
        )
        
        initial_balance = account.balance
        
        calculate_interest()
        
        transactions = Transaction.objects.filter(account=account)
        self.assertEqual(transactions.count(), 1)
        
        transaction = transactions.first()
        self.assertEqual(transaction.transaction_type, INTEREST)
        self.assertGreater(transaction.amount, Decimal('0'))
        
        account.refresh_from_db()
        expected_balance = initial_balance + transaction.amount
        self.assertEqual(account.balance, expected_balance)
        self.assertEqual(transaction.balance_after_transaction, expected_balance)
    
    @patch('transactions.tasks.timezone')
    def test_no_eligible_accounts(self, mock_timezone):
        """Test task when no accounts are eligible."""
        mock_now = datetime(2024, 5, 15, 12, 0, 0)
        mock_timezone.now.return_value = mock_now
        
        calculate_interest()
        
        self.assertEqual(Transaction.objects.count(), 0)
    
    @patch('transactions.tasks.timezone')
    def test_multiple_accounts_processed(self, mock_timezone):
        """Test task processes multiple eligible accounts."""
        mock_now = datetime(2024, 6, 15, 12, 0, 0)
        mock_timezone.now.return_value = mock_now
        
        user1 = User.objects.create_user(email='user1@example.com', password='pass')
        user2 = User.objects.create_user(email='user2@example.com', password='pass')
        
        account1 = UserBankAccount.objects.create(
            user=user1,
            account_type=self.account_type,
            account_no=111111,
            gender='M',
            balance=Decimal('1000.00'),
            interest_start_date=date(2024, 1, 1),
            initial_deposit_date=date(2024, 1, 1)
        )
        
        account2 = UserBankAccount.objects.create(
            user=user2,
            account_type=self.account_type,
            account_no=222222,
            gender='F',
            balance=Decimal('2000.00'),
            interest_start_date=date(2024, 1, 1),
            initial_deposit_date=date(2024, 1, 1)
        )
        
        calculate_interest()
        
        self.assertEqual(Transaction.objects.count(), 2)
        
        account1.refresh_from_db()
        account2.refresh_from_db()
        
        self.assertGreater(account1.balance, Decimal('1000.00'))
        self.assertGreater(account2.balance, Decimal('2000.00'))
    
    @patch('transactions.tasks.timezone')
    def test_account_without_initial_deposit_skipped(self, mock_timezone):
        """Test that accounts without initial deposit date are skipped."""
        mock_now = datetime(2024, 6, 15, 12, 0, 0)
        mock_timezone.now.return_value = mock_now
        
        user = User.objects.create_user(email='test@example.com', password='pass')
        
        UserBankAccount.objects.create(
            user=user,
            account_type=self.account_type,
            account_no=123456,
            gender='M',
            balance=Decimal('1000.00'),
            interest_start_date=date(2024, 1, 1),
            initial_deposit_date=None
        )
        
        calculate_interest()
        
        self.assertEqual(Transaction.objects.count(), 0)
    
    @patch('transactions.tasks.timezone')
    def test_zero_balance_account_skipped(self, mock_timezone):
        """Test that accounts with zero balance are skipped."""
        mock_now = datetime(2024, 6, 15, 12, 0, 0)
        mock_timezone.now.return_value = mock_now
        
        user = User.objects.create_user(email='test@example.com', password='pass')
        
        UserBankAccount.objects.create(
            user=user,
            account_type=self.account_type,
            account_no=123456,
            gender='M',
            balance=Decimal('0.00'),
            interest_start_date=date(2024, 1, 1),
            initial_deposit_date=date(2024, 1, 1)
        )
        
        calculate_interest()
        
        self.assertEqual(Transaction.objects.count(), 0)
