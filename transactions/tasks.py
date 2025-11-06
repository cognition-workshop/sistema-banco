from django.utils import timezone

from celery.decorators import task

from accounts.models import UserBankAccount
from transactions.constants import INTEREST
from transactions.models import Transaction


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
    audit_logs = []

    for account in accounts:
        if this_month in account.get_interest_calculation_months():
            interest = account.account_type.calculate_interest(
                account.balance
            )
            balance_before = account.balance
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
        
        from transactions.models import AuditLog
        for transaction in created_transactions:
            audit_logs.append(AuditLog(
                user=None,
                account=transaction.account,
                transaction=transaction,
                operation_type=INTEREST,
                amount=transaction.amount,
                balance_before=transaction.balance_after_transaction - transaction.amount,
                balance_after=transaction.balance_after_transaction,
                description='Automated interest calculation'
            ))
        
        AuditLog.objects.bulk_create(audit_logs)

    if updated_accounts:
        UserBankAccount.objects.bulk_update(
            updated_accounts, ['balance']
        )
