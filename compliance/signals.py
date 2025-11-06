from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.core.exceptions import PermissionDenied
from transactions.models import Transaction
from .models import ImmutableTransaction, AuditLog


@receiver(post_save, sender=Transaction)
def create_immutable_transaction(sender, instance, created, **kwargs):
    if created:
        ImmutableTransaction.objects.create(
            transaction_id=instance.id,
            account_id=instance.account_id,
            amount=instance.amount,
            balance_after_transaction=instance.balance_after_transaction,
            transaction_type=instance.transaction_type,
            timestamp=instance.timestamp
        )


@receiver(pre_delete, sender=Transaction)
def prevent_transaction_deletion(sender, instance, **kwargs):
    AuditLog.objects.create(
        user=None,
        action='DELETE',
        model_name='Transaction',
        object_id=instance.id,
        previous_value={'attempted_deletion': True},
        new_value={'status': 'prevented'}
    )
    raise PermissionDenied("Transactions cannot be deleted for compliance reasons")
