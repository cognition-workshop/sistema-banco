from django.test import TestCase
from accounts.models import BankAccountType, UserBankAccount, User
from transactions.forms import WithdrawForm
from decimal import Decimal
from django.conf import settings


class WithdrawFormTest(TestCase):
    def setUp(self):
        self.account_type = BankAccountType.objects.create(
            name="Test Account",
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('4.00'),
            interest_calculation_per_year=12
        )
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123"
        )
        account_no = self.user.id + settings.ACCOUNT_NUMBER_START_FROM
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            gender="M",
            birth_date="1990-01-01",
            account_no=account_no,
            balance=Decimal('10000.00')
        )

    def test_withdrawal_exceeds_balance(self):
        self.account.balance = Decimal('100.00')
        self.account.save()
        form = WithdrawForm(
            data={'amount': Decimal('1000.00')},
            account=self.account
        )
        self.assertFalse(form.is_valid())
