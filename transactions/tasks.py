from django.utils import timezone

from celery.decorators import task

from accounts.models import UserBankAccount
from transactions.constants import INTEREST
from transactions.models import Transaction


@task(name="calculate_interest")
def calculate_interest():
    """
    Calcula e aplica juros mensais para contas elegíveis.
    
    Esta tarefa:
    1. Filtra contas com saldo positivo e data de início de juros válida
    2. Verifica se o mês atual é elegível para cálculo de juros
    3. Calcula juros usando o tipo de conta
    4. Atualiza o saldo da conta
    5. Cria transações de juros
    """
    accounts = UserBankAccount.objects.filter(
        balance__gt=0,
        interest_start_date__lte=timezone.now(),
        initial_deposit_date__isnull=False
    ).select_related('account_type')

    created_transactions = []
    updated_accounts = []

    for account in accounts:
        should_calculate, interest_amount = account.get_monthly_interest()
        
        if should_calculate:
            account.apply_interest(interest_amount)
            
            transaction_obj = Transaction.create_interest_transaction(
                account=account,
                amount=interest_amount,
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
