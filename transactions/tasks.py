import logging
from django.db import transaction
from django.utils import timezone

from celery import shared_task

from accounts.models import UserBankAccount
from accounts.utils import is_banking_day
from transactions.constants import INTEREST
from transactions.models import Transaction

logger = logging.getLogger(__name__)


@shared_task(name="calculate_interest")
@transaction.atomic
def calculate_interest():
    """Calculate and apply interest to eligible accounts."""
    today = timezone.now().date()
    
    if not is_banking_day(today):
        return "Not a banking business day"
    
    accounts = UserBankAccount.objects.filter(
        balance__gt=0,
        interest_start_date__lte=today,
        initial_deposit_date__isnull=False
    ).select_related('account_type')

    this_month = today.month

    created_transactions = []
    updated_accounts = []

    for account in accounts:
        if this_month in account.get_interest_calculation_months():
            interest = account.account_type.calculate_interest(account.balance)

            logger.info(
                "Calculating interest",
                extra={
                    "account_no": account.account_no,
                    "current_balance": float(account.balance),
                    "interest": float(interest),
                },
            )

            account.balance += interest

            transaction_obj = Transaction(
                account=account,
                transaction_type=INTEREST,
                amount=interest,
                balance_after_transaction=account.balance,
            )
            created_transactions.append(transaction_obj)
            updated_accounts.append(account)

    if created_transactions:
        Transaction.objects.bulk_create(created_transactions)
        logger.info(
            "Interest calculation completed",
            extra={
                "accounts_processed": len(updated_accounts),
                "total_interest": sum(float(t.amount) for t in created_transactions),
            },
        )

    if updated_accounts:
        UserBankAccount.objects.bulk_update(updated_accounts, ['balance'])
    
    return f"Interest calculated for {len(updated_accounts)} accounts"
