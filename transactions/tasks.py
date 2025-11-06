from django.utils import timezone

from celery import shared_task

from accounts.models import UserBankAccount
from accounts.services import InterestCalculationService
from transactions.constants import INTEREST
from transactions.models import Transaction


@shared_task(name="calculate_interest")
def calculate_interest():
    """
    Celery task to calculate and apply monthly interest to eligible bank accounts.
    
    This task:
    1. Queries all eligible accounts (balance > 0, dates initialized)
    2. Checks if current month matches interest calculation schedule
    3. Calculates interest using InterestCalculationService
    4. Creates interest transactions and updates balances
    5. Uses bulk operations for database efficiency
    """
    accounts = UserBankAccount.objects.filter(
        balance__gt=0,
        interest_start_date__isnull=False,
        initial_deposit_date__isnull=False
    ).select_related('account_type')

    this_month = timezone.now().month

    created_transactions = []
    updated_accounts = []

    for account in accounts:
        interest_months = InterestCalculationService.get_interest_calculation_months(
            account.interest_start_date.month,
            account.account_type.interest_calculation_per_year
        )
        
        if this_month in interest_months:
            interest = InterestCalculationService.calculate_interest(
                account.balance,
                account.account_type.annual_interest_rate,
                account.account_type.interest_calculation_per_year
            )
            
            account.balance += interest
            
            transaction_obj = Transaction(
                account=account,
                transaction_type=INTEREST,
                amount=interest,
                balance_after_transaction=account.balance
            )
            created_transactions.append(transaction_obj)
            updated_accounts.append(account)

    if created_transactions:
        Transaction.objects.bulk_create(created_transactions)

    if updated_accounts:
        UserBankAccount.objects.bulk_update(
            updated_accounts, ['balance']
        )
