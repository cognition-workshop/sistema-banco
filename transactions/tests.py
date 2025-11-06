from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from dateutil.relativedelta import relativedelta

from accounts.models import User, BankAccountType, UserBankAccount
from transactions.models import Transaction
from transactions.constants import INTEREST
from transactions.utils import process_interest_for_accounts


class ProcessInterestForAccountsTestCase(TestCase):
    """Test cases for the process_interest_for_accounts utility function"""
    
    def setUp(self):
        """Set up test data"""
        self.account_type = BankAccountType.objects.create(
            name='Test Savings',
            maximum_withdrawal_amount=Decimal('10000.00'),
            annual_interest_rate=Decimal('12.00'),
            interest_calculation_per_year=12
        )
        
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000001,
            gender='M',
            balance=Decimal('1000.00'),
            initial_deposit_date=timezone.now().date(),
            interest_start_date=timezone.now().date()
        )
    
    def test_process_interest_for_eligible_account(self):
        """Test that interest is calculated for an eligible account in the correct month"""
        current_month = timezone.now().month
        
        self.account.interest_start_date = timezone.now().replace(day=1).date()
        self.account.save()
        
        accounts = UserBankAccount.objects.filter(id=self.account.id)
        
        created_transactions, updated_accounts = process_interest_for_accounts(accounts)
        
        self.assertEqual(len(created_transactions), 1)
        self.assertEqual(len(updated_accounts), 1)
        
        transaction = created_transactions[0]
        self.assertEqual(transaction.account, self.account)
        self.assertEqual(transaction.transaction_type, INTEREST)
        self.assertGreater(transaction.amount, 0)
        
        updated_account = updated_accounts[0]
        expected_balance = Decimal('1000.00') + transaction.amount
        self.assertEqual(updated_account.balance, expected_balance)
    
    def test_no_interest_for_wrong_month(self):
        """Test that no interest is calculated when current month is not an interest month"""
        next_month = timezone.now() + relativedelta(months=1)
        self.account.interest_start_date = next_month.replace(day=1).date()
        self.account.save()
        
        accounts = UserBankAccount.objects.filter(id=self.account.id)
        
        created_transactions, updated_accounts = process_interest_for_accounts(accounts)
        
        self.assertEqual(len(created_transactions), 0)
        self.assertEqual(len(updated_accounts), 0)
    
    def test_process_multiple_accounts(self):
        """Test processing interest for multiple accounts"""
        user2 = User.objects.create_user(
            email='test2@example.com',
            password='testpass123'
        )
        account2 = UserBankAccount.objects.create(
            user=user2,
            account_type=self.account_type,
            account_no=1000002,
            gender='F',
            balance=Decimal('2000.00'),
            initial_deposit_date=timezone.now().date(),
            interest_start_date=timezone.now().date()
        )
        
        accounts = UserBankAccount.objects.filter(
            id__in=[self.account.id, account2.id]
        )
        
        created_transactions, updated_accounts = process_interest_for_accounts(accounts)
        
        self.assertEqual(len(created_transactions), 2)
        self.assertEqual(len(updated_accounts), 2)
    
    def test_balance_after_transaction_is_set(self):
        """Test that balance_after_transaction is correctly set in transaction"""
        self.account.interest_start_date = timezone.now().replace(day=1).date()
        self.account.save()
        
        initial_balance = self.account.balance
        
        accounts = UserBankAccount.objects.filter(id=self.account.id)
        
        created_transactions, updated_accounts = process_interest_for_accounts(accounts)
        
        transaction = created_transactions[0]
        updated_account = updated_accounts[0]
        self.assertEqual(
            transaction.balance_after_transaction,
            updated_account.balance
        )
        self.assertEqual(
            transaction.balance_after_transaction,
            initial_balance + transaction.amount
        )
    
    def test_empty_queryset(self):
        """Test that function handles empty queryset gracefully"""
        accounts = UserBankAccount.objects.none()
        
        created_transactions, updated_accounts = process_interest_for_accounts(accounts)
        
        self.assertEqual(len(created_transactions), 0)
        self.assertEqual(len(updated_accounts), 0)
