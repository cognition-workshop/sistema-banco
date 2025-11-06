import pytest
from django.contrib.auth import get_user_model
from accounts.models import BankAccountType, UserBankAccount, UserAddress
from transactions.models import Transaction
from transactions.constants import DEPOSIT

User = get_user_model()


@pytest.fixture
def bank_account_type():
    return BankAccountType.objects.create(
        name='Savings',
        maximum_withdrawal_amount=10000,
        annual_interest_rate=5.0,
        interest_calculation_per_year=12
    )


@pytest.fixture
def user():
    return User.objects.create_user(
        email='test@example.com',
        password='testpass123',
        first_name='Test',
        last_name='User'
    )


@pytest.fixture
def user_with_account(user, bank_account_type):
    account = UserBankAccount.objects.create(
        user=user,
        account_type=bank_account_type,
        account_no=1000000001,
        gender='M',
        balance=1000
    )
    UserAddress.objects.create(
        user=user,
        street_address='123 Test St',
        city='Test City',
        postal_code=12345,
        country='Test Country'
    )
    return user


@pytest.fixture
def transaction(user_with_account):
    account = user_with_account.account
    return Transaction.objects.create(
        account=account,
        amount=100,
        balance_after_transaction=1100,
        transaction_type=DEPOSIT
    )
