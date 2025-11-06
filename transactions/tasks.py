import logging
from django.utils import timezone
from django.db import transaction, OperationalError, IntegrityError

from celery.decorators import task
from celery.utils.log import get_task_logger

from accounts.models import UserBankAccount
from transactions.constants import INTEREST
from transactions.models import Transaction

logger = get_task_logger(__name__)
audit_logger = logging.getLogger('audit')
transactions_logger = logging.getLogger('transactions')


@task(name="calculate_interest", bind=True, max_retries=3)
def calculate_interest(self):
    """
    Calculate and apply interest to eligible accounts.
    Includes error handling and retry logic with structured logging.
    """
    try:
        transactions_logger.info('Starting interest calculation task')
        
        accounts = UserBankAccount.objects.filter(
            balance__gt=0,
            interest_start_date__gte=timezone.now(),
            initial_deposit_date__isnull=False
        ).select_related('account_type')

        this_month = timezone.now().month
        
        created_transactions = []
        updated_accounts = []
        total_interest = 0

        with transaction.atomic():
            for account in accounts:
                try:
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
                        
                        transactions_logger.info(
                            'Interest calculated and applied',
                            extra={
                                'account_no': account.account_no,
                                'user_email': account.user.email,
                                'amount': interest,
                                'transaction_type': 'INTEREST',
                                'balance_after': account.balance,
                            }
                        )
                        
                except Exception as e:
                    logger.error(
                        f'Error calculating interest for account {account.account_no}: {str(e)}',
                        exc_info=True
                    )
                    continue

            if created_transactions:
                Transaction.objects.bulk_create(created_transactions)
                logger.info(f'Created {len(created_transactions)} interest transactions')

            if updated_accounts:
                UserBankAccount.objects.bulk_update(
                    updated_accounts, ['balance']
                )
                logger.info(f'Updated {len(updated_accounts)} account balances')

        audit_logger.info(
            f'Interest calculation completed',
            extra={
                'action': 'INTEREST_CALCULATION',
                'accounts_processed': len(updated_accounts),
                'total_interest': str(total_interest),
            }
        )
        
        transactions_logger.info(
            'Interest calculation task completed',
            extra={
                'accounts_processed': len(updated_accounts),
                'total_transactions': len(created_transactions),
            }
        )
        
        return {
            'accounts_processed': len(updated_accounts),
            'total_interest': float(total_interest)
        }

    except (OperationalError, IntegrityError) as e:
        logger.error(f'Database error in interest calculation: {str(e)}', exc_info=True)
        audit_logger.error(
            f'Interest calculation failed - Database error',
            extra={
                'action': 'INTEREST_CALCULATION_FAILED',
                'error': str(e),
            }
        )
        raise self.retry(exc=e, countdown=60)
        
    except Exception as e:
        logger.error(f'Unexpected error in interest calculation: {str(e)}', exc_info=True)
        audit_logger.error(
            f'Interest calculation failed - Unexpected error',
            extra={
                'action': 'INTEREST_CALCULATION_FAILED',
                'error': str(e),
            }
        )
        raise self.retry(exc=e, countdown=300)
