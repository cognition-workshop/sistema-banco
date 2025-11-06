from django.utils import timezone

from celery.decorators import task

from accounts.models import UserBankAccount
from transactions.constants import INTEREST
from transactions.models import Transaction, create_audit_log


@task(name="calculate_interest")
def calculate_interest():
    accounts = UserBankAccount.objects.filter(
        balance__gt=0,
        interest_start_date__gte=timezone.now(),
        initial_deposit_date__isnull=False
    ).select_related('account_type', 'user')

    this_month = timezone.now().month

    created_transactions = []
    updated_accounts = []
    balance_snapshots = {}

    for account in accounts:
        if this_month in account.get_interest_calculation_months():
            balance_before = account.balance
            balance_snapshots[account.id] = balance_before
            
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
            updated_accounts.append(account)

    if created_transactions:
        Transaction.objects.bulk_create(created_transactions)
        
        for transaction in created_transactions:
            account = transaction.account
            balance_before = balance_snapshots[account.id]
            create_audit_log(
                user=account.user,
                account=account,
                operation_type='interest',
                amount=transaction.amount,
                balance_before=balance_before,
                balance_after=transaction.balance_after_transaction,
                transaction=transaction,
                ip_address=None,
                user_agent='System - Celery Task'
            )

    if updated_accounts:
        UserBankAccount.objects.bulk_update(
            updated_accounts, ['balance']
        )
