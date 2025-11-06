from celery.decorators import task

from transactions.services import InterestCalculationService


@task(name="calculate_interest")
def calculate_interest():
    """
    Celery task to calculate and apply interest to eligible bank accounts.
    Runs monthly on the 1st at 00:00 UTC via Celery Beat.
    
    This task acts as a thin orchestration layer, delegating the actual
    business logic to InterestCalculationService.
    """
    service = InterestCalculationService()
    return service.calculate_and_apply_interest()
