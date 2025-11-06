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
    ).select_related('account_type').only(
        'id',
        'balance',
        'interest_start_date',
        'account_type__id',
        'account_type__annual_interest_rate',
        'account_type__interest_calculation_per_year'
    )

    this_month = timezone.now().month

    created_transactions = []
    updated_accounts = []

    for account in accounts:
        if this_month in account.get_interest_calculation_months():
            interest = account.account_type.calculate_interest(
                account.balance
            )
            account.balance += interest

            transaction_obj = Transaction(
                account=account,
                transaction_type=INTEREST,
                amount=interest
            )
            created_transactions.append(transaction_obj)
            updated_accounts.append(account)

    BATCH_SIZE = 1000
    if created_transactions:
        for i in range(0, len(created_transactions), BATCH_SIZE):
            batch = created_transactions[i:i + BATCH_SIZE]
            Transaction.objects.bulk_create(batch)

    if updated_accounts:
        UserBankAccount.objects.bulk_update(
            updated_accounts, ['balance']
        )
