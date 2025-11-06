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
    created_audit_logs = []

    for account in accounts:
        if this_month in account.get_interest_calculation_months():
            interest = account.account_type.calculate_interest(
                account.balance
            )
            
            balance_before = account.balance
            account.balance += interest
            balance_after = account.balance
            account.save()

            transaction_obj = Transaction(
                account=account,
                transaction_type=INTEREST,
                amount=interest,
                balance_after_transaction=balance_after
            )
            created_transactions.append(transaction_obj)
            
    if created_transactions:
        Transaction.objects.bulk_create(created_transactions)
        
        from transactions.models import AuditLog
        
        for transaction_obj in created_transactions:
            account = transaction_obj.account
            amount = transaction_obj.amount
            balance_after = transaction_obj.balance_after_transaction
            balance_before = balance_after - amount
            
            created_audit_logs.append(AuditLog(
                account=account,
                action_type=AuditLog.INTEREST,
                amount=amount,
                balance_before=balance_before,
                balance_after=balance_after,
                transaction=transaction_obj,
                user=None,
                metadata={'calculation_month': this_month}
            ))
        
        if created_audit_logs:
            AuditLog.objects.bulk_create(created_audit_logs)
