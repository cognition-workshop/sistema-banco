from django.utils import timezone

from accounts.models import UserBankAccount
from transactions.constants import INTEREST
from transactions.models import Transaction


def process_monthly_interest():
    """
    Process monthly interest calculation for all eligible bank accounts.
    
    This function:
    - Queries accounts eligible for interest calculation
    - Checks if the current month requires interest calculation
    - Calculates interest using the account type's interest rate
    - Updates account balances
    - Creates interest transaction records
    - Uses bulk operations for efficiency
    
    Returns:
        tuple: (number of transactions created, number of accounts updated)
    """
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

    return len(created_transactions), len(updated_accounts)
