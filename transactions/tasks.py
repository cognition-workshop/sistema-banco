from django.utils import timezone

from celery.decorators import task

from accounts.models import UserBankAccount
from transactions.constants import INTEREST, AUDIT_INTEREST
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
    account_balance_before = []

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
            updated_accounts.append(account)
            account_balance_before.append(balance_before)

    if created_transactions:
        Transaction.objects.bulk_create(created_transactions)
        
        for i, transaction in enumerate(created_transactions):
            create_audit_log(
                user=updated_accounts[i].user,
                transaction=transaction,
                action_type=AUDIT_INTEREST,
                balance_before=account_balance_before[i],
                balance_after=updated_accounts[i].balance,
                request=None
            )

    if updated_accounts:
        UserBankAccount.objects.bulk_update(
            updated_accounts, ['balance']
        )
