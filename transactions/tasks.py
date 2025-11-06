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
    failed_accounts = []

    for account in accounts:
        try:
            if this_month in account.get_interest_calculation_months():
                interest = account.account_type.calculate_interest(
                    account.balance
                )
                account.balance += interest
                account.save()

                transaction_obj = Transaction(
                    account=account,
                    transaction_type=INTEREST,
                    amount=interest,
                    balance_after_transaction=account.balance
                )
                created_transactions.append(transaction_obj)

        except Exception as e:
            logger.error(
                f"Erro ao calcular juros para conta {account.id}: {str(e)}",
                exc_info=True,
                extra={'account_id': account.id, 'account_no': account.account_no}
            )
            failed_accounts.append({
                'account_id': account.id,
                'error': str(e)
            })

    if created_transactions:
        Transaction.objects.bulk_create(created_transactions)

    if failed_accounts:
        logger.warning(
            f"Cálculo de juros concluído com {len(failed_accounts)} falhas. "
            f"Total processado com sucesso: {len(created_transactions)}"
        )
