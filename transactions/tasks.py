from django.utils import timezone

from celery import shared_task

from accounts.models import UserBankAccount
from transactions.models import Transaction
from transactions.utils import process_account_interest


@shared_task(name="calculate_interest")
def calculate_interest():
    accounts = UserBankAccount.objects.filter(
        balance__gt=0,
        interest_start_date__isnull=False,
        initial_deposit_date__isnull=False
    ).select_related('account_type')

    this_month = timezone.now().month

    created_transactions = []
    updated_accounts = []

    for account in accounts:
        updated_account, transaction_obj = process_account_interest(
            account, this_month
        )
        
        if transaction_obj is not None:
            created_transactions.append(transaction_obj)
            updated_accounts.append(updated_account)

    if created_transactions:
        Transaction.objects.bulk_create(created_transactions)

    if updated_accounts:
        UserBankAccount.objects.bulk_update(
            updated_accounts, ['balance']
        )
