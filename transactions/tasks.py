import logging

from django.utils import timezone

from celery.decorators import task

from accounts.models import UserBankAccount
from transactions.constants import INTEREST
from transactions.models import Transaction

logger = logging.getLogger(__name__)


@task(name="calculate_interest")
def calculate_interest():
    accounts = UserBankAccount.objects.filter(
        balance__gt=0,
        interest_start_date__gte=timezone.now(),
        initial_deposit_date__isnull=False
    ).select_related('account_type')

    this_month = timezone.now().month

    created_transactions = []
    updated_accounts = []

    for account in accounts:
        try:
            calculation_months = account.get_interest_calculation_months()
            
            if calculation_months is None:
                logger.warning(
                    f"Account {account.account_no}: get_interest_calculation_months() "
                    f"returned None. Skipping interest calculation."
                )
                continue
            
            if not hasattr(calculation_months, '__iter__') or isinstance(calculation_months, str):
                logger.error(
                    f"Account {account.account_no}: get_interest_calculation_months() "
                    f"returned non-iterable type: {type(calculation_months).__name__}. "
                    f"Skipping interest calculation."
                )
                continue
            
            try:
                if not all(isinstance(m, int) and 1 <= m <= 12 for m in calculation_months):
                    logger.error(
                        f"Account {account.account_no}: get_interest_calculation_months() "
                        f"contains invalid month values: {calculation_months}. "
                        f"Skipping interest calculation."
                    )
                    continue
            except TypeError:
                logger.error(
                    f"Account {account.account_no}: get_interest_calculation_months() "
                    f"returned non-comparable values. Skipping interest calculation."
                )
                continue
            
            if this_month not in calculation_months:
                continue
            
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
            
        except AttributeError as e:
            logger.error(
                f"Account {account.account_no}: AttributeError when accessing "
                f"get_interest_calculation_months() or related attributes: {str(e)}. "
                f"Skipping interest calculation.",
                exc_info=True
            )
            continue
        except Exception as e:
            logger.error(
                f"Account {account.account_no}: Unexpected error during interest "
                f"calculation: {str(e)}. Skipping interest calculation.",
                exc_info=True
            )
            continue

    if created_transactions:
        Transaction.objects.bulk_create(created_transactions)

    if updated_accounts:
        UserBankAccount.objects.bulk_update(
            updated_accounts, ['balance']
        )
