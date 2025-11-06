from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from dateutil.relativedelta import relativedelta

from accounts.models import User, BankAccountType, UserBankAccount
from transactions.utils import process_account_interest


class ProcessAccountInterestTests(TestCase):
    """Test cases for the process_account_interest utility function."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        self.account_type = BankAccountType.objects.create(
            name='Savings Account',
            maximum_withdrawal_amount=Decimal('10000.00'),
            annual_interest_rate=Decimal('12.00'),
            interest_calculation_per_year=4
        )
        
        now = timezone.now()
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender='M',
            balance=Decimal('1000.00'),
            initial_deposit_date=now,
            interest_start_date=now
        )
    
    def test_process_interest_in_calculation_month(self):
        """Test that interest is processed when current month is in calculation months."""
        calculation_months = self.account.get_interest_calculation_months()
        current_month = calculation_months[0]
        
        result = process_account_interest(self.account, current_month)
        
        self.assertIsNotNone(result)
        interest, new_balance = result
        
        self.assertGreater(interest, 0)
        
        expected_balance = self.account.balance + interest
        self.assertEqual(new_balance, expected_balance)
    
    def test_process_interest_not_in_calculation_month(self):
        """Test that no interest is processed when current month is not in calculation months."""
        calculation_months = self.account.get_interest_calculation_months()
        non_calculation_month = None
        for month in range(1, 13):
            if month not in calculation_months:
                non_calculation_month = month
                break
        
        result = process_account_interest(self.account, non_calculation_month)
        
        self.assertIsNone(result)
    
    def test_interest_calculation_with_different_balance(self):
        """Test interest calculation with different account balances."""
        self.account.balance = Decimal('5000.00')
        calculation_months = self.account.get_interest_calculation_months()
        current_month = calculation_months[0]
        
        result = process_account_interest(self.account, current_month)
        
        self.assertIsNotNone(result)
        interest, new_balance = result
        
        self.assertGreater(interest, 0)
        self.assertEqual(new_balance, Decimal('5000.00') + interest)
    
    def test_interest_with_zero_balance(self):
        """Test interest calculation with zero balance."""
        self.account.balance = Decimal('0.00')
        calculation_months = self.account.get_interest_calculation_months()
        current_month = calculation_months[0]
        
        result = process_account_interest(self.account, current_month)
        
        self.assertIsNotNone(result)
        interest, new_balance = result
        
        self.assertEqual(interest, Decimal('0.00'))
        self.assertEqual(new_balance, Decimal('0.00'))
