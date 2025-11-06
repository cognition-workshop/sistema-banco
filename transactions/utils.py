from django.utils import timezone
from decimal import Decimal

from accounts.models import UserBankAccount
from transactions.constants import INTEREST
from transactions.models import Transaction


def apply_monthly_interest(current_month=None):
    """
    Apply interest to eligible bank accounts for the specified month.
    
    This function handles the business logic of calculating and applying
    interest to bank accounts based on their account type configuration.
    
    Args:
        current_month (int, optional): The month number (1-12) to calculate 
                                      interest for. Defaults to current month.
    
    Returns:
        dict: A dictionary containing:
            - 'transactions_created': Number of transaction records created
            - 'accounts_updated': Number of accounts updated
            - 'total_interest': Total interest amount applied across all accounts
    """
    if current_month is None:
        current_month = timezone.now().month
    
    accounts = UserBankAccount.objects.filter(
        balance__gt=0,
        interest_start_date__lte=timezone.now(),
        initial_deposit_date__isnull=False
    ).select_related('account_type')
    
    created_transactions = []
    updated_accounts = []
    total_interest = Decimal('0.00')
    
    for account in accounts:
        if current_month in account.get_interest_calculation_months():
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
        'transactions_created': len(created_transactions),
        'accounts_updated': len(updated_accounts),
        'total_interest': total_interest
    }
