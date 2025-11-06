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

            audit_log_obj = AuditLog(
                user=None,
                account=account,
                operation_type=INTEREST,
                amount=interest,
                balance_before=balance_before,
                balance_after=account.balance,
                ip_address=None,
                metadata={'automated': True, 'month': this_month}
            )
            created_audit_logs.append(audit_log_obj)

    if created_transactions:
        Transaction.objects.bulk_create(created_transactions)

    if created_audit_logs:
        AuditLog.objects.bulk_create(created_audit_logs)

    if updated_accounts:
        UserBankAccount.objects.bulk_update(
            updated_accounts, ['balance']
        )
