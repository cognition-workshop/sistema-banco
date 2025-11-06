from django.db import models
from django.conf import settings
from django.core.exceptions import PermissionDenied
from accounts.models import UserBankAccount
from transactions.models import Transaction


class AuditLog(models.Model):
    EVENT_TRANSACTION_CREATE = 'TRANSACTION_CREATE'
    EVENT_TRANSACTION_MODIFY = 'TRANSACTION_MODIFY'
    EVENT_ACCOUNT_CREATE = 'ACCOUNT_CREATE'
    EVENT_ACCOUNT_MODIFY = 'ACCOUNT_MODIFY'
    EVENT_ACCOUNT_SUSPEND = 'ACCOUNT_SUSPEND'
    EVENT_FRAUD_ALERT = 'FRAUD_ALERT'
    EVENT_LOGIN_SUCCESS = 'LOGIN_SUCCESS'
    EVENT_LOGIN_FAILURE = 'LOGIN_FAILURE'
    
    EVENT_TYPE_CHOICES = [
        (EVENT_TRANSACTION_CREATE, 'Transação Criada'),
        (EVENT_TRANSACTION_MODIFY, 'Transação Modificada'),
        (EVENT_ACCOUNT_CREATE, 'Conta Criada'),
        (EVENT_ACCOUNT_MODIFY, 'Conta Modificada'),
        (EVENT_ACCOUNT_SUSPEND, 'Conta Suspensa'),
        (EVENT_FRAUD_ALERT, 'Alerta de Fraude'),
        (EVENT_LOGIN_SUCCESS, 'Login Bem-sucedido'),
        (EVENT_LOGIN_FAILURE, 'Tentativa de Login Falhou'),
    ]
    
    event_type = models.CharField(max_length=50, choices=EVENT_TYPE_CHOICES)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs'
    )
    account = models.ForeignKey(
        UserBankAccount,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs'
    )
    transaction = models.ForeignKey(
        Transaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs'
    )
    
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    description = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Log de Auditoria'
        verbose_name_plural = 'Logs de Auditoria'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['event_type', '-timestamp']),
            models.Index(fields=['account', '-timestamp']),
        ]
    
    def __str__(self):
        return f'{self.get_event_type_display()} - {self.timestamp.strftime("%d/%m/%Y %H:%M:%S")}'
    
    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise PermissionDenied('Logs de auditoria são imutáveis e não podem ser modificados.')
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        raise PermissionDenied('Logs de auditoria são imutáveis e não podem ser deletados.')
