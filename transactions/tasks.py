import logging
from django.utils import timezone

from celery.decorators import task

from accounts.models import UserBankAccount
from transactions.constants import INTEREST
from transactions.models import Transaction


@task(name="calculate_interest")
def calculate_interest():
    logger = logging.getLogger('transactions')
    logger.info('Starting interest calculation task')
    
    accounts = UserBankAccount.objects.filter(
        balance__gt=0,
        interest_start_date__gte=timezone.now(),
        initial_deposit_date__isnull=False
    ).select_related('account_type')

    this_month = timezone.now().month

    created_transactions = []
    updated_accounts = []

    for account in accounts:
        if this_month in account.get_interest_calculation_months():
            interest = account.account_type.calculate_interest(
                account.balance
            )
            account.balance += interest
            account.save()

            logger.info(
                'Interest calculated and applied',
                extra={
                    'account_no': account.account_no,
                    'user_email': account.user.email,
                    'interest_amount': interest,
                    'transaction_type': 'INTEREST',
                    'balance_after': account.balance,
                }
            )

            transaction_obj = Transaction(
                account=account,
                transaction_type=INTEREST,
                amount=interest
            )
            created_transactions.append(transaction_obj)
            updated_accounts.append(account)

    if created_transactions:
        Transaction.objects.bulk_create(created_transactions)

    if updated_accounts:
        UserBankAccount.objects.bulk_update(
            updated_accounts, ['balance']
        )
    
    logger.info(
        'Interest calculation task completed',
        extra={
            'accounts_processed': len(updated_accounts),
            'total_transactions': len(created_transactions),
        }
    )
