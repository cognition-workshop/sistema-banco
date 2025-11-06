from django.utils import timezone

from celery.decorators import task

from accounts.models import UserBankAccount
from transactions.constants import INTEREST
from transactions.models import Transaction
from core.utils.brazilian_calendar import BrazilianBankingCalendar


@task(name="calculate_interest")
def calculate_interest():
    """Calculate interest only on business days."""
    now = timezone.now()
    
    if not BrazilianBankingCalendar.is_business_day(now):
        return "Not a business day - skipping interest calculation"
    
    accounts = UserBankAccount.objects.filter(
        balance__gt=0,
        interest_start_date__lte=now,
        initial_deposit_date__isnull=False
    ).select_related('account_type')

    this_month = now.month

    created_transactions = []
    updated_accounts = []

    for account in accounts:
        if this_month in account.get_interest_calculation_months():
            interest = account.account_type.calculate_interest(
                account.balance
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
    
    return f"Calculated interest for {len(updated_accounts)} accounts"
