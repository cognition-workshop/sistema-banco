from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal

from celery.decorators import task

from accounts.models import UserBankAccount
from transactions.constants import INTEREST
from transactions.models import Transaction
from utils.brazilian_calendar import count_business_days


@task(name="calculate_interest")
def calculate_interest():
    accounts = UserBankAccount.objects.filter(
        balance__gt=0,
        interest_start_date__lte=timezone.now(),
        initial_deposit_date__isnull=False
    ).select_related('account_type')

    this_month = timezone.now().month
    current_date = timezone.now()
    
    first_day = datetime(current_date.year, current_date.month, 1)
    if current_date.month == 12:
        last_day = datetime(current_date.year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = datetime(current_date.year, current_date.month + 1, 1) - timedelta(days=1)
    
    business_days_in_month = count_business_days(first_day, last_day)
    
    expected_business_days = 21
    business_days_ratio = Decimal(business_days_in_month) / Decimal(expected_business_days)

    created_transactions = []
    updated_accounts = []

    for account in accounts:
        if this_month in account.get_interest_calculation_months():
            interest = account.account_type.calculate_interest(
                account.balance,
                business_days_ratio=float(business_days_ratio)
            )
            account.balance += interest

            transaction_obj = Transaction(
                account=account,
                transaction_type=INTEREST,
                amount=interest,
                balance_after_transaction=account.balance
            )
            created_transactions.append(transaction_obj)
            updated_accounts.append(account)

    if created_transactions:
        Transaction.objects.bulk_create(created_transactions)

    if updated_accounts:
        UserBankAccount.objects.bulk_update(
            updated_accounts, ['balance']
        )
