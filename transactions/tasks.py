from django.utils import timezone

from celery.decorators import task

from accounts.models import UserBankAccount
from transactions.constants import INTEREST
from transactions.models import Transaction
import logging

logger = logging.getLogger('celery')


@task(name="calculate_interest")
def calculate_interest():
    logger.info("Starting interest calculation task")
    start_time = timezone.now()
    
    accounts = UserBankAccount.objects.filter(
        balance__gt=0,
        interest_start_date__gte=timezone.now(),
        initial_deposit_date__isnull=False
    ).select_related('account_type')

    this_month = timezone.now().month
    logger.info(f"Found {accounts.count()} accounts for potential interest calculation")

    created_transactions = []
    updated_accounts = []

    for account in accounts:
        if this_month in account.get_interest_calculation_months():
            interest = account.account_type.calculate_interest(
                account.balance
            )
            account.balance += interest
            account.save()

            logger.info(
                f"Calculated interest for account {account.account_no}: "
                f"interest=${interest}, new_balance=${account.balance}"
            )

            transaction_obj = Transaction(
                account=account,
                transaction_type=INTEREST,
                amount=interest
            )
            created_transactions.append(transaction_obj)
            updated_accounts.append(account)

    if created_transactions:
        Transaction.objects.bulk_create(created_transactions)

    if updated_accounts:
        UserBankAccount.objects.bulk_update(
            updated_accounts, ['balance']
        )
    
    duration = (timezone.now() - start_time).total_seconds()
    logger.info(
        f"Interest calculation completed: {len(created_transactions)} transactions created, "
        f"duration={duration:.2f}s"
    )
