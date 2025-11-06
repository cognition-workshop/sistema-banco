from decimal import Decimal
from django.test import TestCase
from django.utils import timezone

from accounts.models import User, BankAccountType, UserBankAccount
from transactions.constants import INTEREST
from transactions.models import Transaction
from transactions.utils import process_account_interest


class ProcessAccountInterestTestCase(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        self.account_type = BankAccountType.objects.create(
            name='Savings Account',
            maximum_withdrawal_amount=Decimal('10000.00'),
            annual_interest_rate=Decimal('5.00'),
            interest_calculation_per_year=4
        )
        
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1234567890,
            gender='M',
            balance=Decimal('1000.00'),
            initial_deposit_date=timezone.now().date(),
            interest_start_date=timezone.now().replace(month=3, day=1).date()
        )
    
    def test_process_interest_in_calculation_month(self):
        transaction_obj, updated_account = process_account_interest(
            self.account, 3
        )
        
        self.assertIsNotNone(transaction_obj)
        self.assertEqual(transaction_obj.account, self.account)
        self.assertEqual(transaction_obj.transaction_type, INTEREST)
        self.assertGreater(transaction_obj.amount, 0)
        
        self.assertIsNotNone(updated_account)
        self.assertEqual(updated_account, self.account)
        self.assertGreater(updated_account.balance, Decimal('1000.00'))
        
        expected_interest = self.account_type.calculate_interest(Decimal('1000.00'))
        self.assertEqual(transaction_obj.amount, expected_interest)
        self.assertEqual(updated_account.balance, Decimal('1000.00') + expected_interest)
    
    def test_no_process_interest_not_in_calculation_month(self):
        transaction_obj, updated_account = process_account_interest(
            self.account, 1
        )
        
        self.assertIsNone(transaction_obj)
        self.assertIsNone(updated_account)
        
        self.assertEqual(self.account.balance, Decimal('1000.00'))
    
    def test_interest_calculation_with_different_months(self):
        original_balance = self.account.balance
        calculation_months = self.account.get_interest_calculation_months()
        
        for month in calculation_months:
            self.account.balance = original_balance
            
            transaction_obj, updated_account = process_account_interest(
                self.account, month
            )
            
            self.assertIsNotNone(transaction_obj)
            self.assertIsNotNone(updated_account)
            self.assertGreater(updated_account.balance, original_balance)
    
    def test_interest_with_zero_balance(self):
        self.account.balance = Decimal('0.00')
        
        transaction_obj, updated_account = process_account_interest(
            self.account, 3
        )
        
        self.assertIsNotNone(transaction_obj)
        self.assertEqual(transaction_obj.amount, Decimal('0.00'))
        self.assertEqual(updated_account.balance, Decimal('0.00'))
