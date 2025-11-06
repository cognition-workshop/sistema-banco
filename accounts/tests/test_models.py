from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from accounts.models import BankAccountType, UserBankAccount
from django.conf import settings

User = get_user_model()

class BankAccountTypeModelTest(TestCase):
    def setUp(self):
        self.account_type = BankAccountType.objects.create(
            name="Savings Test",
            maximum_withdrawal_amount=Decimal('20000.00'),
            annual_interest_rate=Decimal('5.00'),
            interest_calculation_per_year=12
        )
    
    def test_calculate_interest_monthly(self):
        principal = Decimal('1000.00')
        interest = self.account_type.calculate_interest(principal)
        self.assertAlmostEqual(float(interest), 4.17, places=2)

class UserBankAccountModelTest(TestCase):
    def setUp(self):
        self.account_type = BankAccountType.objects.create(
            name="Current Account",
            maximum_withdrawal_amount=Decimal('50000.00'),
            annual_interest_rate=Decimal('3.00'),
            interest_calculation_per_year=4
        )
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123"
        )
    
    def test_account_number_generation(self):
        account_no = self.user.id + settings.ACCOUNT_NUMBER_START_FROM
        account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            gender="M",
            birth_date="1990-01-01",
            account_no=account_no
        )
        self.assertEqual(account.account_no, account_no)
