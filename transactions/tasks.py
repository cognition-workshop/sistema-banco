import logging
from django.utils import timezone

from celery.decorators import task

from accounts.models import UserBankAccount
from transactions.constants import INTEREST
from transactions.models import Transaction

logger = logging.getLogger(__name__)


@task(name="calculate_interest")
def calculate_interest():
    logger.info("Starting interest calculation task")
    
    accounts = UserBankAccount.objects.filter(
        balance__gt=0,
        interest_start_date__gte=timezone.now(),
        initial_deposit_date__isnull=False
    ).select_related('account_type')

    this_month = timezone.now().month
    accounts_processed = 0

    created_transactions = []
    updated_accounts = []

    for account in accounts:
        if this_month in account.get_interest_calculation_months():
            try:
                interest = account.account_type.calculate_interest(
                    account.balance
                )
                account.balance += interest
                account.save()

                transaction_obj = Transaction(
                    account=account,
                    transaction_type=INTEREST,
                    amount=interest
                )
                created_transactions.append(transaction_obj)
                updated_accounts.append(account)
                accounts_processed += 1
                
                logger.info(f"Interest calculated for account {account.account_no}: ${interest}")
            except Exception as e:
                logger.error(f"Interest calculation failed for account {account.account_no}: {str(e)}", exc_info=True)

    if created_transactions:
        Transaction.objects.bulk_create(created_transactions)

    if updated_accounts:
        UserBankAccount.objects.bulk_update(
            updated_accounts, ['balance']
        )
    
    logger.info(f"Interest calculation task completed. Processed {accounts_processed} accounts")
