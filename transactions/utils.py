from django.utils import timezone

from accounts.models import UserBankAccount
from transactions.constants import INTEREST
from transactions.models import Transaction


def process_interest_calculation(accounts_queryset=None, current_month=None):
    """
    Process interest calculation for eligible accounts.
    
    This function encapsulates the business logic for calculating and applying
    interest to bank accounts. It can be called by the Celery task or used
    independently for testing and other purposes.
    
    Args:
        accounts_queryset: Optional queryset of UserBankAccount objects to process.
                          If None, will query all eligible accounts.
        current_month: Optional month number (1-12) to check against calculation months.
                      If None, will use the current month.
    
    Returns:
        tuple: (created_transactions, updated_accounts) - lists of Transaction and
               UserBankAccount objects that were processed
    """
    if accounts_queryset is None:
        accounts_queryset = UserBankAccount.objects.filter(
            balance__gt=0,
            interest_start_date__lte=timezone.now(),
            initial_deposit_date__isnull=False
        ).select_related('account_type')
    
    if current_month is None:
        current_month = timezone.now().month

    created_transactions = []
    updated_accounts = []

    for account in accounts_queryset:
        if current_month in account.get_interest_calculation_months():
            interest = account.account_type.calculate_interest(
                account.balance
            )
            account.balance += interest

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

    if updated_accounts:
        UserBankAccount.objects.bulk_update(
            updated_accounts, ['balance']
        )

    return created_transactions, updated_accounts
