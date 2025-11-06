from celery import shared_task

from transactions.utils import process_monthly_interest


@shared_task(name="calculate_interest")
def calculate_interest():
    return process_monthly_interest()
