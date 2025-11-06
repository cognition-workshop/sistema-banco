from celery import shared_task

from transactions.utils import calculate_interest_for_accounts


@shared_task(name="calculate_interest")
def calculate_interest():
    """
    Celery task to calculate interest for all eligible accounts.
    
    This task is scheduled to run monthly via Celery Beat.
    """
    transactions_created, accounts_updated = calculate_interest_for_accounts()
    return f"Interest calculated: {transactions_created} transactions created, {accounts_updated} accounts updated"
