from django.db.models.signals import post_save
from django.dispatch import receiver
from transactions.models import Transaction
from .models import AuditLog


@receiver(post_save, sender=Transaction)
def audit_transaction(sender, instance, created, **kwargs):
    """Automatically create audit log for transactions"""
    if created:
        AuditLog.objects.create(
            usuario=instance.account.user,
            tipo_transacao=f'TRANSACTION_{instance.get_transaction_type_display().upper()}',
            dados_transacao={
                'transaction_id': instance.id,
                'account_no': str(instance.account.account_no),
                'amount': str(instance.amount),
                'balance_after': str(instance.balance_after_transaction),
                'transaction_type': instance.transaction_type,
                'timestamp': instance.timestamp.isoformat(),
            }
        )
