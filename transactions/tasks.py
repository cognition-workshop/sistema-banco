from django.utils import timezone

from celery.decorators import task

from accounts.models import UserBankAccount
from transactions.constants import INTEREST
from transactions.models import Transaction, AuditLog


@task(name="calculate_interest")
def calculate_interest():
    accounts = UserBankAccount.objects.filter(
        balance__gt=0,
        interest_start_date__lte=timezone.now(),
        initial_deposit_date__isnull=False
    ).select_related('account_type')

    this_month = timezone.now().month

    created_transactions = []
    updated_accounts = []

    for account in accounts:
        if this_month in account.get_interest_calculation_months():
            old_balance = account.balance
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

            AuditLog.objects.create(
                user=account.user,
                action='INTEREST_CALCULATION',
                model_name='UserBankAccount',
                object_id=account.id,
                changes={'old_balance': str(old_balance), 'new_balance': str(account.balance), 'interest': str(interest)},
                description=f'Interest {interest}$ calculated for account {account.account_no}'
            )

    if created_transactions:
        Transaction.objects.bulk_create(created_transactions)

    if updated_accounts:
        UserBankAccount.objects.bulk_update(
            updated_accounts, ['balance']
        )
