from celery.decorators import task

from transactions.utils import process_interest_calculation


@task(name="calculate_interest")
def calculate_interest():
    process_interest_calculation()
