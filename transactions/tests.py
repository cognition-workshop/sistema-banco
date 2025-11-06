from decimal import Decimal
from datetime import date

from django.test import TestCase

from accounts.models import User, BankAccountType, UserBankAccount
from transactions.utils import process_interest_for_accounts


class ProcessInterestForAccountsTests(TestCase):
    """Test suite for the process_interest_for_accounts utility function."""
    
    def setUp(self):
        """Set up test data."""
        self.savings_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('10000.00'),
            annual_interest_rate=Decimal('5.00'),
            interest_calculation_per_year=12
        )
        
        self.current_type = BankAccountType.objects.create(
            name='Current',
            maximum_withdrawal_amount=Decimal('50000.00'),
            annual_interest_rate=Decimal('3.00'),
            interest_calculation_per_year=4
        )
        
        self.user1 = User.objects.create_user(email='user1@test.com', password='pass123')
        self.account1 = UserBankAccount.objects.create(
            user=self.user1,
            account_type=self.savings_type,
            account_no=1000000001,
            gender='M',
            balance=Decimal('1000.00'),
            interest_start_date=date(2024, 1, 1),
            initial_deposit_date=date(2024, 1, 1)
        )
        
        self.user2 = User.objects.create_user(email='user2@test.com', password='pass123')
        self.account2 = UserBankAccount.objects.create(
            user=self.user2,
            account_type=self.current_type,
            account_no=1000000002,
            gender='F',
            balance=Decimal('5000.00'),
            interest_start_date=date(2024, 1, 1),
            initial_deposit_date=date(2024, 1, 1)
        )
    
    def test_account_eligible_in_calculation_month(self):
        """Test that accounts receive interest in their calculation month."""
        accounts = [self.account1]
        result = process_interest_for_accounts(accounts, current_month=1)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], self.account1)
        self.assertGreater(result[0][1], 0)
    
    def test_account_not_eligible_outside_calculation_month(self):
        """Test that accounts don't receive interest outside calculation months."""
        accounts = [self.account2]
        result = process_interest_for_accounts(accounts, current_month=2)
        
        self.assertEqual(len(result), 0)
    
    def test_multiple_accounts_mixed_eligibility(self):
        """Test processing multiple accounts with different eligibilities."""
        accounts = [self.account1, self.account2]
        result = process_interest_for_accounts(accounts, current_month=1)
        
        self.assertEqual(len(result), 2)
        
        result = process_interest_for_accounts(accounts, current_month=2)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], self.account1)
    
    def test_interest_calculation_accuracy(self):
        """Test that interest is calculated correctly."""
        accounts = [self.account1]
        result = process_interest_for_accounts(accounts, current_month=1)
        
        account, interest = result[0]
        expected_interest = Decimal('4.17')
        self.assertEqual(interest, expected_interest)
    
    def test_empty_accounts_list(self):
        """Test handling of empty accounts list."""
        result = process_interest_for_accounts([], current_month=1)
        self.assertEqual(len(result), 0)
    
    def test_all_months_for_quarterly_account(self):
        """Test quarterly calculation months are correct."""
        accounts = [self.account2]
        
        eligible_months = [1, 4, 7, 10]
        ineligible_months = [2, 3, 5, 6, 8, 9, 11, 12]
        
        for month in eligible_months:
            result = process_interest_for_accounts(accounts, current_month=month)
            self.assertEqual(len(result), 1, f"Should be eligible in month {month}")
        
        for month in ineligible_months:
            result = process_interest_for_accounts(accounts, current_month=month)
            self.assertEqual(len(result), 0, f"Should not be eligible in month {month}")
