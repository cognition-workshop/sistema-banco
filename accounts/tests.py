from django.test import TestCase
from django.contrib.auth import get_user_model
from django.conf import settings
from decimal import Decimal

from accounts.models import BankAccountType, UserBankAccount, UserAddress
from accounts.forms import UserRegistrationForm

User = get_user_model()


class UserModelTest(TestCase):
    def setUp(self):
        self.account_type = BankAccountType.objects.create(
            name='Test Savings',
            maximum_withdrawal_amount=5000,
            annual_interest_rate=5.0,
            interest_calculation_per_year=12
        )
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender='M',
            balance=1000.00
        )
    
    def test_user_balance_property(self):
        self.assertEqual(self.user.balance, Decimal('1000.00'))
    
    def test_user_without_account_balance(self):
        user_no_account = User.objects.create_user(
            email='noaccount@example.com',
            password='testpass123'
        )
        self.assertEqual(user_no_account.balance, 0)


class AccountNumberGenerationTest(TestCase):
    def setUp(self):
        self.account_type = BankAccountType.objects.create(
            name='Test Savings',
            maximum_withdrawal_amount=5000,
            annual_interest_rate=5.0,
            interest_calculation_per_year=12
        )
    
    def test_unique_account_numbers(self):
        users = []
        for i in range(5):
            form_data = {
                'first_name': f'User{i}',
                'last_name': f'Test{i}',
                'email': f'user{i}@example.com',
                'password1': 'testpass123',
                'password2': 'testpass123',
                'account_type': self.account_type.id,
                'gender': 'M',
                'birth_date': '1990-01-01'
            }
            form = UserRegistrationForm(data=form_data)
            self.assertTrue(form.is_valid())
            user = form.save()
            users.append(user)
        
        account_numbers = [u.account.account_no for u in users]
        self.assertEqual(len(account_numbers), len(set(account_numbers)))
        
        for num in account_numbers:
            self.assertGreaterEqual(num, settings.ACCOUNT_NUMBER_START_FROM)
