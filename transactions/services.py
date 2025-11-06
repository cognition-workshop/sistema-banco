from django.utils import timezone

from accounts.models import UserBankAccount
from transactions.constants import INTEREST
from transactions.models import Transaction


class InterestCalculationService:
    """
    Service class to handle interest calculation logic for bank accounts.
    Separates business logic from Celery task orchestration.
    """

    def __init__(self):
        self.current_month = timezone.now().month

    def get_eligible_accounts(self):
        """
        Filter and return accounts eligible for interest calculation.
        
        Returns accounts that:
        - Have positive balance
        - Have started accruing interest (interest_start_date in the past)
        - Have made an initial deposit
        """
        return UserBankAccount.objects.filter(
            balance__gt=0,
            interest_start_date__lte=timezone.now(),
            initial_deposit_date__isnull=False
        ).select_related('account_type')

    def is_month_eligible(self, account):
        """
        Check if the current month is eligible for interest calculation
        for the given account.
        """
        return self.current_month in account.get_interest_calculation_months()

    def calculate_and_apply_interest(self):
        """
        Main method to calculate and apply interest to all eligible accounts.
        
        Returns:
            dict: Summary with counts of processed accounts and transactions
        """
        accounts = self.get_eligible_accounts()
        
        created_transactions = []
        updated_accounts = []

        for account in accounts:
            if self.is_month_eligible(account):
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

        return {
            'accounts_processed': len(updated_accounts),
            'transactions_created': len(created_transactions)
        }
