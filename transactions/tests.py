from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from datetime import date

from accounts.models import User, BankAccountType, UserBankAccount
from transactions.constants import INTEREST
from transactions.utils import process_interest_for_accounts


class ProcessInterestForAccountsTest(TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.savings_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('5.00'),
            interest_calculation_per_year=12
        )
        
        self.current_type = BankAccountType.objects.create(
            name='Current',
            maximum_withdrawal_amount=Decimal('10000.00'),
            annual_interest_rate=Decimal('3.00'),
            interest_calculation_per_year=4
        )
        
        self.user1 = User.objects.create_user(
            email='user1@test.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            email='user2@test.com',
            password='testpass123'
        )
        self.user3 = User.objects.create_user(
            email='user3@test.com',
            password='testpass123'
        )

    def test_interest_calculated_for_eligible_account_in_correct_month(self):
        """Test that interest is calculated for accounts in their interest month"""
        account = UserBankAccount.objects.create(
            user=self.user1,
            account_type=self.savings_type,
            account_no=1000001,
            balance=Decimal('1000.00'),
            interest_start_date=date(2024, 1, 15),
            initial_deposit_date=date(2024, 1, 15)
        )
        
        accounts = UserBankAccount.objects.filter(id=account.id)
        transactions, updated_accounts = process_interest_for_accounts(accounts, 1)
        
        self.assertEqual(len(transactions), 1)
        self.assertEqual(len(updated_accounts), 1)
        
        transaction = transactions[0]
        self.assertEqual(transaction.account, account)
        self.assertEqual(transaction.transaction_type, INTEREST)
        self.assertGreater(transaction.amount, 0)
        
        updated_account = updated_accounts[0]
        expected_balance = Decimal('1000.00') + transaction.amount
        self.assertEqual(updated_account.balance, expected_balance)

    def test_no_interest_for_wrong_month(self):
        """Test that no interest is calculated for accounts not in their interest month"""
        account = UserBankAccount.objects.create(
            user=self.user1,
            account_type=self.current_type,
            account_no=1000001,
            balance=Decimal('1000.00'),
            interest_start_date=date(2024, 1, 15),
            initial_deposit_date=date(2024, 1, 15)
        )
        
        accounts = UserBankAccount.objects.filter(id=account.id)
        transactions, updated_accounts = process_interest_for_accounts(accounts, 2)
        
        self.assertEqual(len(transactions), 0)
        self.assertEqual(len(updated_accounts), 0)

    def test_multiple_accounts_processed_correctly(self):
        """Test that multiple accounts are processed correctly"""
        account1 = UserBankAccount.objects.create(
            user=self.user1,
            account_type=self.savings_type,
            account_no=1000001,
            balance=Decimal('1000.00'),
            interest_start_date=date(2024, 1, 15),
            initial_deposit_date=date(2024, 1, 15)
        )
        
        account2 = UserBankAccount.objects.create(
            user=self.user2,
            account_type=self.savings_type,
            account_no=1000002,
            balance=Decimal('2000.00'),
            interest_start_date=date(2024, 1, 15),
            initial_deposit_date=date(2024, 1, 15)
        )
        
        accounts = UserBankAccount.objects.filter(
            id__in=[account1.id, account2.id]
        )
        transactions, updated_accounts = process_interest_for_accounts(accounts, 1)
        
        self.assertEqual(len(transactions), 2)
        self.assertEqual(len(updated_accounts), 2)
        
        for transaction in transactions:
            self.assertEqual(transaction.transaction_type, INTEREST)
            self.assertGreater(transaction.amount, 0)

    def test_mixed_accounts_some_eligible_some_not(self):
        """Test processing accounts where only some are eligible for current month"""
        account1 = UserBankAccount.objects.create(
            user=self.user1,
            account_type=self.savings_type,
            account_no=1000001,
            balance=Decimal('1000.00'),
            interest_start_date=date(2024, 1, 15),
            initial_deposit_date=date(2024, 1, 15)
        )
        
        account2 = UserBankAccount.objects.create(
            user=self.user2,
            account_type=self.current_type,
            account_no=1000002,
            balance=Decimal('2000.00'),
            interest_start_date=date(2024, 1, 15),
            initial_deposit_date=date(2024, 1, 15)
        )
        
        accounts = UserBankAccount.objects.filter(
            id__in=[account1.id, account2.id]
        )
        transactions, updated_accounts = process_interest_for_accounts(accounts, 2)
        
        self.assertEqual(len(transactions), 1)
        self.assertEqual(len(updated_accounts), 1)
        self.assertEqual(transactions[0].account, account1)

    def test_balance_after_transaction_set_correctly(self):
        """Test that balance_after_transaction is set correctly in transaction objects"""
        account = UserBankAccount.objects.create(
            user=self.user1,
            account_type=self.savings_type,
            account_no=1000001,
            balance=Decimal('1000.00'),
            interest_start_date=date(2024, 1, 15),
            initial_deposit_date=date(2024, 1, 15)
        )
        
        initial_balance = account.balance
        
        accounts = UserBankAccount.objects.filter(id=account.id)
        transactions, updated_accounts = process_interest_for_accounts(accounts, 1)
        
        transaction = transactions[0]
        updated_account = updated_accounts[0]
        
        expected_balance = initial_balance + transaction.amount
        self.assertEqual(transaction.balance_after_transaction, expected_balance)
        self.assertEqual(updated_account.balance, expected_balance)

    def test_empty_queryset_returns_empty_lists(self):
        """Test that processing an empty queryset returns empty lists"""
        accounts = UserBankAccount.objects.none()
        transactions, updated_accounts = process_interest_for_accounts(accounts, 1)
        
        self.assertEqual(len(transactions), 0)
        self.assertEqual(len(updated_accounts), 0)
