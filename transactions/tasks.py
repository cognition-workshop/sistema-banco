from celery.decorators import task

from transactions.utils import process_interest_calculation


@task(name="calculate_interest")
def calculate_interest():
    """
    Celery task to calculate and apply interest to eligible bank accounts.
    
    This is a thin wrapper around the process_interest_calculation utility function.
    """
    return process_interest_calculation()
