from decimal import Decimal
from datetime import date

from django.test import TestCase
from django.utils import timezone

from accounts.models import User, BankAccountType, UserBankAccount
from transactions.utils import calculate_account_interest


class CalculateAccountInterestTests(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        self.savings_account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('10000.00'),
            annual_interest_rate=Decimal('5.00'),
            interest_calculation_per_year=12
        )
        
        self.current_account_type = BankAccountType.objects.create(
            name='Current',
            maximum_withdrawal_amount=Decimal('50000.00'),
            annual_interest_rate=Decimal('3.00'),
            interest_calculation_per_year=4
        )
    
    def test_calculate_interest_when_month_matches(self):
        account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.savings_account_type,
            account_no=1000000001,
            gender='M',
            balance=Decimal('1000.00'),
            interest_start_date=date(2024, 1, 1),
            initial_deposit_date=date(2024, 1, 1)
        )
        
        interest = calculate_account_interest(account, 1)
        
        expected_interest = Decimal('4.17')
        self.assertIsNotNone(interest)
        self.assertEqual(interest, expected_interest)
    
    def test_no_interest_when_month_does_not_match(self):
        account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.savings_account_type,
            account_no=1000000002,
            gender='M',
            balance=Decimal('1000.00'),
            interest_start_date=date(2024, 1, 1),
            initial_deposit_date=date(2024, 1, 1)
        )
        
        account.interest_start_date = date(2024, 3, 1)
        account.save()
        
        interest = calculate_account_interest(account, 1)
        self.assertIsNone(interest)
    
    def test_quarterly_interest_calculation(self):
        account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.current_account_type,
            account_no=1000000003,
            gender='F',
            balance=Decimal('5000.00'),
            interest_start_date=date(2024, 1, 1),
            initial_deposit_date=date(2024, 1, 1)
        )
        
        interest = calculate_account_interest(account, 4)
        
        expected_interest = Decimal('37.50')
        self.assertIsNotNone(interest)
        self.assertEqual(interest, expected_interest)
        
        interest_feb = calculate_account_interest(account, 2)
        self.assertIsNone(interest_feb)
    
    def test_different_interest_rates(self):
        savings_account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.savings_account_type,
            account_no=1000000004,
            gender='M',
            balance=Decimal('1000.00'),
            interest_start_date=date(2024, 1, 1),
            initial_deposit_date=date(2024, 1, 1)
        )
        
        user2 = User.objects.create_user(email='test2@example.com', password='test')
        current_account = UserBankAccount.objects.create(
            user=user2,
            account_type=self.current_account_type,
            account_no=1000000005,
            gender='F',
            balance=Decimal('1000.00'),
            interest_start_date=date(2024, 1, 1),
            initial_deposit_date=date(2024, 1, 1)
        )
        
        savings_interest = calculate_account_interest(savings_account, 1)
        current_interest = calculate_account_interest(current_account, 1)
        
        self.assertIsNotNone(savings_interest)
        self.assertIsNotNone(current_interest)
        
        self.assertEqual(savings_interest, Decimal('4.17'))
        self.assertEqual(current_interest, Decimal('7.50'))
