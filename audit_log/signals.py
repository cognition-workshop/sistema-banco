from django.db.models.signals import post_save
from django.dispatch import receiver
from transactions.models import Transaction
from accounts.models import UserBankAccount
from .models import AuditLog
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Transaction)
def log_transaction_create(sender, instance, created, **kwargs):
    if created:
        try:
            AuditLog.objects.create(
                event_type=AuditLog.EVENT_TRANSACTION_CREATE,
                user=instance.account.user if hasattr(instance.account, 'user') else None,
                account=instance.account,
                transaction=instance,
                description=f'Transação {instance.get_transaction_type_display()} criada: R$ {instance.amount}',
                metadata={
                    'transaction_type': instance.transaction_type,
                    'amount': str(instance.amount),
                    'balance_after': str(instance.balance_after_transaction),
                }
            )
        except Exception as e:
            logger.error(f'Error creating audit log for transaction {instance.id}: {str(e)}')


@receiver(post_save, sender=UserBankAccount)
def log_account_create(sender, instance, created, **kwargs):
    if created:
        try:
            AuditLog.objects.create(
                event_type=AuditLog.EVENT_ACCOUNT_CREATE,
                user=instance.user if hasattr(instance, 'user') else None,
                account=instance,
                description=f'Conta bancária criada: #{instance.account_no}',
                metadata={
                    'account_no': instance.account_no,
                    'account_type': instance.account_type.name if instance.account_type else None,
                    'initial_balance': str(instance.balance),
                }
            )
        except Exception as e:
            logger.error(f'Error creating audit log for account {instance.id}: {str(e)}')
