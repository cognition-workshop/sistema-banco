import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from accounts.models import UserBankAccount, BankAccountType

User = get_user_model()


@pytest.fixture
def bank_account_type(db):
    return BankAccountType.objects.create(
        name='Savings',
        maximum_withdrawal_amount=Decimal('5000.00'),
        annual_interest_rate=Decimal('5.0'),
        interest_calculation_per_year=12
    )


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
def demo_user(db):
    user, created = User.objects.get_or_create(
        email='demo@example.com',
        defaults={'password': 'demopass123'}
    )
    if not created:
        user.set_password('demopass123')
        user.save()
    return user


@pytest.fixture
def user_account(db, user, bank_account_type):
    return UserBankAccount.objects.create(
        user=user,
        account_type=bank_account_type,
        account_no=1000000001,
        gender='M',
        balance=Decimal('100.00')
    )


@pytest.fixture
def demo_account(db, demo_user, bank_account_type):
    account, created = UserBankAccount.objects.get_or_create(
        user=demo_user,
        defaults={
            'account_type': bank_account_type,
            'account_no': 9999999999,
            'gender': 'M',
            'balance': Decimal('100.00')
        }
    )
    if not created:
        account.balance = Decimal('100.00')
        account.save()
    return account


@pytest.fixture
def account_factory(db, bank_account_type):
    def create_account(balance=Decimal('100.00'), email=None):
        if email is None:
            import time
            email = f'test{int(time.time() * 1000000)}@example.com'
        
        user = User.objects.create_user(
            email=email,
            password='testpass123'
        )
        return UserBankAccount.objects.create(
            user=user,
            account_type=bank_account_type,
            account_no=1000000000 + user.id,
            gender='M',
            balance=balance
        )
    return create_account
