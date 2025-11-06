from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Transaction, AuditLog


@receiver(post_save, sender=Transaction)
def create_transaction_audit_log(sender, instance, created, **kwargs):
    """
    Creates an audit log entry for every transaction
    """
    if created:
        AuditLog.objects.create(
            transaction=instance,
            user=instance.account.user,
            action='TRANSACTION_CREATED',
            data_snapshot={
                'account_id': instance.account.id,
                'amount': str(instance.amount),
                'balance_after': str(instance.balance_after_transaction),
                'type': instance.transaction_type,
                'timestamp': instance.timestamp.isoformat()
            }
        )
