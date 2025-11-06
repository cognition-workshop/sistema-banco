from django.utils import timezone

from celery import shared_task

from accounts.models import UserBankAccount
from transactions.constants import INTEREST
from transactions.models import Transaction
from transactions.utils import process_interest_for_accounts


@shared_task(name="calculate_interest")
def calculate_interest():
    """
    Celery task to calculate and apply interest to eligible bank accounts.
    
    This task queries accounts that are eligible for interest calculation,
    processes them using the utility function, and performs bulk database
    operations to create transactions and update account balances.
    """
    accounts = UserBankAccount.objects.filter(
        balance__gt=0,
        interest_start_date__lte=timezone.now(),
        initial_deposit_date__isnull=False
    ).select_related('account_type')

    current_month = timezone.now().month

    transaction_data, account_updates = process_interest_for_accounts(
        list(accounts), 
        current_month
    )

    if transaction_data:
        transaction_objects = [
            Transaction(**data) for data in transaction_data
        ]
        Transaction.objects.bulk_create(transaction_objects)

    if account_updates:
        for update in account_updates:
            update['account'].balance = update['new_balance']
        
        accounts_to_update = [update['account'] for update in account_updates]
        UserBankAccount.objects.bulk_update(accounts_to_update, ['balance'])
