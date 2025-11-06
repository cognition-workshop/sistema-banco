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
    ).select_related('account_type', 'user')

    this_month = timezone.now().month

    created_transactions = []
    updated_accounts = []
    audit_logs = []

    for account in accounts:
        if this_month in account.get_interest_calculation_months():
            balance_before = account.balance
            
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
            
            audit_logs.append({
                'account': account,
                'balance_before': balance_before,
                'balance_after': account.balance,
                'amount': interest,
            })

    if created_transactions:
        Transaction.objects.bulk_create(created_transactions)
        
        from transactions.models import AuditLog
        audit_log_objects = []
        for i, transaction in enumerate(created_transactions):
            audit_data = audit_logs[i]
            audit_log_objects.append(AuditLog(
                user=audit_data['account'].user,
                account=audit_data['account'],
                transaction=transaction,
                action_type=AuditLog.INTEREST,
                amount=audit_data['amount'],
                balance_before=audit_data['balance_before'],
                balance_after=audit_data['balance_after']
            ))
        AuditLog.objects.bulk_create(audit_log_objects)

    if updated_accounts:
        UserBankAccount.objects.bulk_update(
            updated_accounts, ['balance']
        )
