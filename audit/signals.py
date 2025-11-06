from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType

from transactions.models import Transaction
from accounts.models import UserBankAccount
from .models import AuditLog
from .middleware import get_current_user, get_client_ip


def serialize_instance(instance):
    from decimal import Decimal
    data = {}
    for field in instance._meta.fields:
        value = getattr(instance, field.name)
        if hasattr(value, 'isoformat'):
            value = value.isoformat()
        elif hasattr(value, 'pk'):
            value = value.pk
        elif isinstance(value, Decimal):
            value = str(value)
        data[field.name] = value
    return data


def create_audit_log(instance, action, old_value=None):
    content_type = ContentType.objects.get_for_model(instance)
    new_value = serialize_instance(instance) if action != AuditLog.ACTION_DELETE else None
    
    user = get_current_user()
    ip_address = get_client_ip()
    
    if not ip_address:
        ip_address = '0.0.0.0'
    
    AuditLog.objects.create(
        user=user,
        action=action,
        content_type=content_type,
        object_id=instance.pk,
        old_value=old_value,
        new_value=new_value,
        ip_address=ip_address,
    )


@receiver(post_save, sender=Transaction)
def audit_transaction_save(sender, instance, created, **kwargs):
    action = AuditLog.ACTION_CREATE if created else AuditLog.ACTION_UPDATE
    old_value = None
    if not created:
        pass
    
    create_audit_log(instance, action, old_value)


@receiver(post_delete, sender=Transaction)
def audit_transaction_delete(sender, instance, **kwargs):
    old_value = serialize_instance(instance)
    create_audit_log(instance, AuditLog.ACTION_DELETE, old_value)


@receiver(post_save, sender=UserBankAccount)
def audit_account_save(sender, instance, created, **kwargs):
    action = AuditLog.ACTION_CREATE if created else AuditLog.ACTION_UPDATE
    old_value = None
    if not created:
        pass
    
    create_audit_log(instance, action, old_value)


@receiver(post_delete, sender=UserBankAccount)
def audit_account_delete(sender, instance, **kwargs):
    old_value = serialize_instance(instance)
    create_audit_log(instance, AuditLog.ACTION_DELETE, old_value)
