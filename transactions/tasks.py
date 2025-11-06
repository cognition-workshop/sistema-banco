from django.utils import timezone

from celery import shared_task

from accounts.models import UserBankAccount
from transactions.models import Transaction
from transactions.utils import process_interest_for_accounts


@shared_task(name="calculate_interest")
def calculate_interest():
    accounts = UserBankAccount.objects.filter(
        balance__gt=0,
        interest_start_date__gte=timezone.now(),
        initial_deposit_date__isnull=False
    ).select_related('account_type')

    this_month = timezone.now().month

    created_transactions, updated_accounts = process_interest_for_accounts(
        list(accounts), this_month
    )

    if created_transactions:
        Transaction.objects.bulk_create(created_transactions)

    if updated_accounts:
        UserBankAccount.objects.bulk_update(
            updated_accounts, ['balance']
        )
