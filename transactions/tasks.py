from django.utils import timezone
import logging

from celery.decorators import task

from accounts.models import UserBankAccount
from transactions.constants import INTEREST
from transactions.models import Transaction

logger = logging.getLogger(__name__)


@task(name="calculate_interest")
def calculate_interest():
    now = timezone.now()
    current_month = now.month
    current_year = now.year
    
    existing_interest_transactions = Transaction.objects.filter(
        transaction_type=INTEREST,
        timestamp__year=current_year,
        timestamp__month=current_month
    ).exists()
    
    if existing_interest_transactions:
        logger.warning(
            f"Juros já foram calculados para {current_month}/{current_year}. "
            "Abortando execução para prevenir duplicação."
        )
        return {
            'success': False,
            'reason': 'already_processed',
            'month': current_month,
            'year': current_year
        }
    
    logger.info(f"Iniciando cálculo de juros para {current_month}/{current_year}")
    
    accounts = UserBankAccount.objects.filter(
        balance__gt=0,
        interest_start_date__gte=timezone.now(),
        initial_deposit_date__isnull=False
    ).select_related('account_type')

    this_month = timezone.now().month

    created_transactions = []
    updated_accounts = []

    for account in accounts:
        if this_month in account.get_interest_calculation_months():
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

    if created_transactions:
        Transaction.objects.bulk_create(created_transactions)

    if updated_accounts:
        UserBankAccount.objects.bulk_update(
            updated_accounts, ['balance']
        )
