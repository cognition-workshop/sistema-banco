from django.utils import timezone

from celery.decorators import task

from accounts.models import UserBankAccount
from transactions.constants import INTEREST
from transactions.models import Transaction
from transactions.utils import process_interest_for_accounts


@task(name="calculate_interest")
def calculate_interest():
    accounts = UserBankAccount.objects.filter(
        balance__gt=0,
        interest_start_date__gte=timezone.now(),
        initial_deposit_date__isnull=False
    ).select_related('account_type')

    current_month = timezone.now().month
    
    eligible_accounts = process_interest_for_accounts(accounts, current_month)

    created_transactions = []
    updated_accounts = []

    for account, interest in eligible_accounts:
        account.balance += interest
        account.save()

        transaction_obj = Transaction(
            account=account,
            transaction_type=INTEREST,
            amount=interest
        )
        created_transactions.append(transaction_obj)
        updated_accounts.append(account)

    if created_transactions:
        Transaction.objects.bulk_create(created_transactions)

    if updated_accounts:
        UserBankAccount.objects.bulk_update(
            updated_accounts, ['balance']
        )
