from django.utils import timezone
from django.contrib.auth import get_user_model

from celery.decorators import task

from accounts.models import UserBankAccount
from transactions.constants import INTEREST
from transactions.models import Transaction


@task(name="calculate_interest")
def calculate_interest():
    User = get_user_model()
    
    system_user, _ = User.objects.get_or_create(
        email='system@banco.internal',
        defaults={
            'first_name': 'System',
            'last_name': 'Automated',
            'is_active': False,
        }
    )
    
    accounts = UserBankAccount.objects.filter(
        balance__gt=0,
        interest_start_date__lte=timezone.now(),
        initial_deposit_date__isnull=False
    ).select_related('account_type')

    this_month = timezone.now().month

    for account in accounts:
        if this_month in account.get_interest_calculation_months():
            previous_balance = account.balance
            interest = account.account_type.calculate_interest(account.balance)
            
            account.balance += interest
            account.save(update_fields=['balance'])

            Transaction.objects.create(
                account=account,
                transaction_type=INTEREST,
                amount=interest,
                previous_balance=previous_balance,
                balance_after_transaction=account.balance,
                user=system_user,
                ip_address=None,
                metadata={
                    'task_name': 'calculate_interest',
                    'calculation_month': this_month,
                    'automated': True,
                }
            )
