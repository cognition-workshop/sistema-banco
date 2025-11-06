from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.forms.models import model_to_dict
from accounts.models import User, UserBankAccount
from transactions.models import Transaction, ChavePix
from .models import AuditLog

MONITORED_MODELS = [User, UserBankAccount, Transaction, ChavePix]


@receiver(post_save)
def audit_save(sender, instance, created, **kwargs):
    if sender not in MONITORED_MODELS:
        return
    
    try:
        from threading import current_thread
        request = getattr(current_thread(), 'request', None)
        if not request:
            return
        
        acao = 'CREATE' if created else 'UPDATE'
        
        AuditLog.objects.create(
            user=request.user if request.user.is_authenticated else None,
            acao=acao,
            modelo=sender.__name__,
            objeto_id=instance.pk,
            dados_novos=model_to_dict(instance),
            ip_address=getattr(request, '_audit_ip', '127.0.0.1'),
            user_agent=getattr(request, '_audit_user_agent', '')
        )
    except Exception:
        pass


@receiver(post_delete)
def audit_delete(sender, instance, **kwargs):
    if sender not in MONITORED_MODELS:
        return
    
    try:
        from threading import current_thread
        request = getattr(current_thread(), 'request', None)
        if not request:
            return
        
        AuditLog.objects.create(
            user=request.user if request.user.is_authenticated else None,
            acao='DELETE',
            modelo=sender.__name__,
            objeto_id=instance.pk,
            dados_anteriores=model_to_dict(instance),
            ip_address=getattr(request, '_audit_ip', '127.0.0.1'),
            user_agent=getattr(request, '_audit_user_agent', '')
        )
    except Exception:
        pass
