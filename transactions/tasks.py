from celery.decorators import task

from transactions.utils import apply_monthly_interest


@task(name="calculate_interest")
def calculate_interest():
    """
    Celery task to calculate and apply monthly interest to eligible accounts.
    
    Scheduled to run monthly on the 1st day at midnight.
    """
    apply_monthly_interest()
