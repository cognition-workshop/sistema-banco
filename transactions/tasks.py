from celery.decorators import task

from transactions.utils import process_interest_calculation


@task(name="calculate_interest")
def calculate_interest():
    """
    Celery task wrapper for interest calculation.
    
    Delegates to process_interest_calculation() utility function.
    """
    return process_interest_calculation()
