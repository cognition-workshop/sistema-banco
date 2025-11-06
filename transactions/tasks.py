from django.utils import timezone

from celery.decorators import task

from accounts.models import UserBankAccount
from transactions.constants import INTEREST
from transactions.models import Transaction, AuditLog


@task(name="calculate_interest")
def calculate_interest():
    accounts = UserBankAccount.objects.filter(
        balance__gt=0,
        interest_start_date__gte=timezone.now(),
        initial_deposit_date__isnull=False
    ).select_related('account_type')

    this_month = timezone.now().month

    created_transactions = []
    created_audit_logs = []
    updated_accounts = []
    balance_tracking = {}

    for account in accounts:
        if this_month in account.get_interest_calculation_months():
            balance_before = account.balance
            balance_tracking[account.id] = balance_before
            
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
        
        latest_transactions = Transaction.objects.filter(
            transaction_type=INTEREST,
            timestamp__gte=timezone.now().replace(hour=0, minute=0, second=0)
        ).select_related('account')
        
        for transaction in latest_transactions:
            if transaction.account.id in balance_tracking:
                balance_before = balance_tracking[transaction.account.id]
                created_audit_logs.append(
                    AuditLog(
                        user=transaction.account.user,
                        account=transaction.account,
                        transaction=transaction,
                        operation_type=INTEREST,
                        amount=transaction.amount,
                        balance_before=balance_before,
                        balance_after=transaction.balance_after_transaction,
                        description=f'Interest calculation of ${transaction.amount}'
                    )
                )
        
        if created_audit_logs:
            AuditLog.objects.bulk_create(created_audit_logs)

    if updated_accounts:
        UserBankAccount.objects.bulk_update(
            updated_accounts, ['balance']
        )
