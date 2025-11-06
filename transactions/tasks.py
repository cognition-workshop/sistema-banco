from django.utils import timezone

from celery.decorators import task

from transactions.utils import process_monthly_interest


@task(name="calculate_interest")
def calculate_interest():
    process_monthly_interest(now=timezone.now())
