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
    audit_log_data = []

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
                amount=interest,
                balance_after_transaction=account.balance
            )
            created_transactions.append(transaction_obj)
            
            audit_log_data.append({
                'account': account,
                'balance_before': balance_before,
                'balance_after': account.balance,
                'amount': interest,
            })

    if created_transactions:
        Transaction.objects.bulk_create(created_transactions)
        
        from transactions.models import create_audit_log
        for i, transaction in enumerate(created_transactions):
            data = audit_log_data[i]
            create_audit_log(
                account=data['account'],
                transaction_type=INTEREST,
                amount=data['amount'],
                balance_before=data['balance_before'],
                balance_after=data['balance_after'],
                transaction=transaction,
                metadata={'source': 'system', 'task': 'calculate_interest'}
            )

    if accounts:
        UserBankAccount.objects.bulk_update(
            list(accounts), ['balance']
        )
