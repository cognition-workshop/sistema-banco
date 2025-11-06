from celery.decorators import task

from transactions.utils import process_monthly_interest


@task(name="calculate_interest")
def calculate_interest():
    transactions_created, accounts_updated = process_monthly_interest()
    return {
        'transactions_created': transactions_created,
        'accounts_updated': accounts_updated
    }
