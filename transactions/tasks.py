from django.utils import timezone
import logging

from celery.decorators import task

from accounts.models import UserBankAccount
from transactions.constants import INTEREST
from transactions.models import Transaction

logger = logging.getLogger('transactions')


@task(name="calculate_interest")
def calculate_interest():
    logger.info("Starting monthly interest calculation task")
    
    accounts = UserBankAccount.objects.filter(
        balance__gt=0,
        interest_start_date__gte=timezone.now(),
        initial_deposit_date__isnull=False
    ).select_related('account_type')

    this_month = timezone.now().month
    logger.debug(f"Processing interest for month: {this_month}")

    created_transactions = []
    updated_accounts = []
    total_interest = 0

    for account in accounts:
        if this_month in account.get_interest_calculation_months():
            interest = account.account_type.calculate_interest(
                account.balance
            )
            account.balance += interest
            account.save()

            logger.debug(
                f"Interest calculated for account {account.account_no}: "
                f"${interest}, new balance ${account.balance}"
            )

            transaction_obj = Transaction(
                account=account,
                transaction_type=INTEREST,
                amount=interest
            )
            created_transactions.append(transaction_obj)
            updated_accounts.append(account)
            total_interest += interest

    if created_transactions:
        Transaction.objects.bulk_create(created_transactions)

    if updated_accounts:
        UserBankAccount.objects.bulk_update(
            updated_accounts, ['balance']
        )
    
    logger.info(
        f"Interest calculation completed: {len(updated_accounts)} accounts processed, "
        f"total interest ${total_interest:.2f}"
    )
