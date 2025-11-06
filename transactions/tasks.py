from django.utils import timezone

from celery.decorators import task

from accounts.models import UserBankAccount
from transactions.models import Transaction
from transactions.utils import process_interest_for_accounts


@task(name="calculate_interest")
def calculate_interest():
    """
    Celery task to calculate and apply interest to eligible accounts.
    
    Runs monthly to process interest for accounts that have:
    - Positive balance
    - Interest start date in the past
    - Initial deposit date set
    """
    accounts = UserBankAccount.objects.filter(
        balance__gt=0,
        interest_start_date__lte=timezone.now(),
        initial_deposit_date__isnull=False
    ).select_related('account_type')
    
    created_transactions, updated_accounts = process_interest_for_accounts(accounts)
    
    if created_transactions:
        Transaction.objects.bulk_create(created_transactions)
    
    if updated_accounts:
        UserBankAccount.objects.bulk_update(
            updated_accounts, ['balance']
        )
