from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from accounts.models import UserBankAccount
from transactions.models import Transaction
from .models import BacenAuditLog

User = get_user_model()


def get_previous_hash():
    """Get hash from the most recent log entry"""
    last_log = BacenAuditLog.objects.order_by('-timestamp').first()
    return last_log.hash_integridade if last_log else None


@receiver(post_save, sender=User)
def log_user_changes(sender, instance, created, **kwargs):
    """Log user creation/updates"""
    evento_tipo = 'USER_CREATED' if created else 'USER_UPDATED'
    
    BacenAuditLog.objects.create(
        evento_tipo=evento_tipo,
        usuario=instance,
        dados_posteriores={
            'email': instance.email,
            'first_name': instance.first_name,
            'last_name': instance.last_name,
        },
        hash_anterior=get_previous_hash()
    )


@receiver(post_save, sender=UserBankAccount)
def log_account_changes(sender, instance, created, **kwargs):
    """Log account creation/updates"""
    evento_tipo = 'ACCOUNT_CREATED' if created else 'ACCOUNT_UPDATED'
    
    BacenAuditLog.objects.create(
        evento_tipo=evento_tipo,
        usuario=instance.user,
        conta_afetada=instance,
        dados_posteriores={
            'account_no': instance.account_no,
            'balance': str(instance.balance),
            'agencia': instance.agencia,
            'conta': instance.conta,
        },
        hash_anterior=get_previous_hash()
    )


@receiver(post_save, sender=Transaction)
def log_transaction(sender, instance, created, **kwargs):
    """Log transaction creation"""
    if created:
        BacenAuditLog.objects.create(
            evento_tipo='TRANSACTION_CREATED',
            usuario=instance.account.user,
            conta_afetada=instance.account,
            dados_posteriores={
                'transaction_type': instance.transaction_type,
                'amount': str(instance.amount),
                'balance_after': str(instance.balance_after_transaction),
            },
            hash_anterior=get_previous_hash()
        )
