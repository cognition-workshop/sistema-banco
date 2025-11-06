#!/usr/bin/env python
"""Create demo data for the banking system"""
import os
import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "banking_system.settings")
django.setup()

from django.utils import timezone  # noqa: E402
from dateutil.relativedelta import relativedelta  # noqa: E402
from accounts.models import User, BankAccountType, UserBankAccount, UserAddress  # noqa: E402
from transactions.models import Transaction  # noqa: E402
from transactions.constants import DEPOSIT, WITHDRAWAL  # noqa: E402

# Create Bank Account Types
savings_type, _ = BankAccountType.objects.get_or_create(
    name="Savings Account",
    defaults={
        "maximum_withdrawal_amount": 5000.00,
        "annual_interest_rate": 5.00,
        "interest_calculation_per_year": 12,
    },
)

current_type, _ = BankAccountType.objects.get_or_create(
    name="Current Account",
    defaults={
        "maximum_withdrawal_amount": 10000.00,
        "annual_interest_rate": 2.50,
        "interest_calculation_per_year": 6,
    },
)

# Create Demo User
demo_user, created = User.objects.get_or_create(
    email="demo@example.com",
    defaults={
        "first_name": "John",
        "last_name": "Doe",
    },
)

if created:
    demo_user.set_password("demo123")
    demo_user.save()

# Create Bank Account
account, _ = UserBankAccount.objects.get_or_create(
    user=demo_user,
    defaults={
        "account_type": savings_type,
        "account_no": 1001,
        "gender": "M",
        "birth_date": "1990-01-01",
        "balance": 5000.00,
        "initial_deposit_date": timezone.now() - relativedelta(months=6),
        "interest_start_date": timezone.now() + relativedelta(months=1),
    },
)

# Create Address
address, _ = UserAddress.objects.get_or_create(
    user=demo_user,
    defaults={
        "street_address": "123 Main Street",
        "city": "New York",
        "postal_code": 10001,
        "country": "USA",
    },
)

# Create some transactions
transactions_data = [
    (DEPOSIT, 1000.00, timezone.now() - relativedelta(days=30)),
    (DEPOSIT, 2000.00, timezone.now() - relativedelta(days=25)),
    (WITHDRAWAL, 500.00, timezone.now() - relativedelta(days=20)),
    (DEPOSIT, 1500.00, timezone.now() - relativedelta(days=15)),
    (WITHDRAWAL, 200.00, timezone.now() - relativedelta(days=10)),
    (DEPOSIT, 800.00, timezone.now() - relativedelta(days=5)),
    (WITHDRAWAL, 300.00, timezone.now() - relativedelta(days=2)),
]

# Delete old transactions for demo user
Transaction.objects.filter(account=account).delete()

balance = 0
for trans_type, amount, timestamp in transactions_data:
    if trans_type == DEPOSIT:
        balance += amount
    else:
        balance -= amount

    Transaction.objects.create(
        account=account,
        amount=amount,
        balance_after_transaction=balance,
        transaction_type=trans_type,
        timestamp=timestamp,
    )

# Update final balance
account.balance = balance
account.save()

print("✅ Demo data created successfully!")
print("Demo User: demo@example.com / demo123")
print(f"Account Number: {account.account_no}")
print(f"Balance: ${account.balance}")
print(f"Transactions: {Transaction.objects.filter(account=account).count()}")
