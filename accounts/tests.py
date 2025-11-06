from django.test import TestCase
from django.conf import settings
from decimal import Decimal

from accounts.models import User, UserBankAccount, BankAccountType
from accounts.forms import UserRegistrationForm


class UserBalancePropertyTest(TestCase):
    
    def setUp(self):
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('5.0'),
            interest_calculation_per_year=12
        )
    
    def test_balance_with_account(self):
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        account = UserBankAccount.objects.create(
            user=user,
            account_type=self.account_type,
            account_no=settings.ACCOUNT_NUMBER_START_FROM,
            gender='M',
            balance=Decimal('1000.00')
        )
        
        self.assertEqual(user.balance, Decimal('1000.00'))
    
    def test_balance_without_account(self):
        user = User.objects.create_user(
            email='test2@example.com',
            password='testpass123'
        )
        
        self.assertEqual(user.balance, 0)


class AccountNumberGenerationTest(TestCase):
    
    def setUp(self):
        self.account_type = BankAccountType.objects.create(
            name='Checking',
            maximum_withdrawal_amount=Decimal('10000.00'),
            annual_interest_rate=Decimal('3.0'),
            interest_calculation_per_year=4
        )
    
    def test_first_account_number(self):
        form_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com',
            'password1': 'securepass123',
            'password2': 'securepass123',
            'account_type': self.account_type.id,
            'gender': 'M',
            'birth_date': '1990-01-01'
        }
        
        form = UserRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())
        user = form.save()
        
        self.assertEqual(
            user.account.account_no,
            settings.ACCOUNT_NUMBER_START_FROM
        )
    
    def test_sequential_account_numbers(self):
        user1 = User.objects.create_user(
            email='user1@example.com',
            password='pass123'
        )
        account1 = UserBankAccount.objects.create(
            user=user1,
            account_type=self.account_type,
            account_no=settings.ACCOUNT_NUMBER_START_FROM,
            gender='M'
        )
        
        form_data = {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'email': 'jane@example.com',
            'password1': 'securepass123',
            'password2': 'securepass123',
            'account_type': self.account_type.id,
            'gender': 'F',
            'birth_date': '1992-05-15'
        }
        
        form = UserRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())
        user2 = form.save()
        
        self.assertEqual(
            user2.account.account_no,
            account1.account_no + 1
        )
    
    def test_account_number_uniqueness(self):
        for i in range(3):
            form_data = {
                'first_name': f'User{i}',
                'last_name': 'Test',
                'email': f'user{i}@example.com',
                'password1': 'securepass123',
                'password2': 'securepass123',
                'account_type': self.account_type.id,
                'gender': 'M',
                'birth_date': '1990-01-01'
            }
            
            form = UserRegistrationForm(data=form_data)
            self.assertTrue(form.is_valid())
            form.save()
        
        account_numbers = list(
            UserBankAccount.objects.values_list('account_no', flat=True)
        )
        self.assertEqual(len(account_numbers), len(set(account_numbers)))
