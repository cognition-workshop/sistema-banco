import logging
from decimal import Decimal
from time import time

from django.utils import timezone

from celery.decorators import task

from accounts.models import UserBankAccount
from transactions.constants import INTEREST
from transactions.models import Transaction

logger = logging.getLogger(__name__)


@task(name="calculate_interest")
def calculate_interest():
    start_time = time()
    logger.info("="*50)
    logger.info("Iniciando cálculo mensal de juros")
    logger.info(f"Data/hora: {timezone.now()}")
    
    accounts = UserBankAccount.objects.filter(
        balance__gt=0,
        interest_start_date__gte=timezone.now(),
        initial_deposit_date__isnull=False
    ).select_related('account_type')
    
    total_eligible = accounts.count()
    logger.info(f"Total de contas elegíveis: {total_eligible}")

    this_month = timezone.now().month

    created_transactions = []
    updated_accounts = []
    total_interest_amount = Decimal('0.00')

    for account in accounts:
        try:
            if this_month in account.get_interest_calculation_months():
                interest = account.account_type.calculate_interest(
                    account.balance
                )
                account.balance += interest
                total_interest_amount += interest

                transaction_obj = Transaction(
                    account=account,
                    transaction_type=INTEREST,
                    amount=interest,
                    balance_after_transaction=account.balance
                )
                created_transactions.append(transaction_obj)
                updated_accounts.append(account)
                
        except Exception as e:
            logger.error(
                f"Erro ao processar conta {account.id}: {str(e)}",
                exc_info=True
            )

    if created_transactions:
        Transaction.objects.bulk_create(created_transactions)
        logger.info(f"Criadas {len(created_transactions)} transações de juros")

    if updated_accounts:
        UserBankAccount.objects.bulk_update(
            updated_accounts, ['balance']
        )
        logger.info(f"Atualizadas {len(updated_accounts)} contas")
    
    elapsed_time = time() - start_time
    logger.info("="*50)
    logger.info("Cálculo de juros concluído com sucesso")
    logger.info(f"Contas processadas: {len(updated_accounts)}/{total_eligible}")
    logger.info(f"Total de juros calculados: R$ {total_interest_amount:.2f}")
    logger.info(f"Tempo de execução: {elapsed_time:.2f} segundos")
    logger.info("="*50)
    
    return {
        'success': True,
        'total_eligible': total_eligible,
        'processed': len(updated_accounts),
        'total_interest': float(total_interest_amount),
        'elapsed_time': elapsed_time
    }
