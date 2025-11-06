from django.utils import timezone

from accounts.models import UserBankAccount
from transactions.constants import INTEREST
from transactions.models import Transaction


def process_interest_calculation():
    """
    Process interest calculation for eligible bank accounts.
    
    This function:
    1. Queries accounts eligible for interest calculation
    2. Checks if current month is an interest calculation month for each account
    3. Calculates and applies interest
    4. Creates transaction records
    5. Performs bulk updates for efficiency
    
    Returns:
        dict: Dictionary containing:
            - 'accounts_processed': number of accounts that received interest
            - 'total_interest': total interest amount distributed
    """
    accounts = UserBankAccount.objects.filter(
        balance__gt=0,
        interest_start_date__lte=timezone.now(),
        initial_deposit_date__isnull=False
    ).select_related('account_type')

    this_month = timezone.now().month

    created_transactions = []
    updated_accounts = []
    total_interest = 0

    for account in accounts:
        if this_month in account.get_interest_calculation_months():
            interest = account.account_type.calculate_interest(
                account.balance
            )
            account.balance += interest
            total_interest += interest

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

    return {
        'accounts_processed': len(updated_accounts),
        'total_interest': float(total_interest)
    }
