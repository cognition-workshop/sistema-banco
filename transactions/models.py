from django.db import models

from .constants import TRANSACTION_TYPE_CHOICES
from accounts.models import UserBankAccount


class Transaction(models.Model):
    account = models.ForeignKey(
        UserBankAccount,
        related_name='transactions',
        on_delete=models.CASCADE,
    )
    amount = models.DecimalField(
        decimal_places=2,
        max_digits=12
    )
    balance_after_transaction = models.DecimalField(
        decimal_places=2,
        max_digits=12
    )
    transaction_type = models.PositiveSmallIntegerField(
        choices=TRANSACTION_TYPE_CHOICES
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.account.account_no)

    class Meta:
        ordering = ['timestamp']


class AuditLog(models.Model):
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.PROTECT,
        related_name='audit_logs',
        help_text='User who initiated the transaction'
    )
    
    transaction = models.ForeignKey(
        Transaction,
        on_delete=models.PROTECT,
        related_name='audit_logs',
        help_text='Associated transaction record'
    )
    
    action_type = models.CharField(
        max_length=50,
        help_text='Type of action performed (e.g., deposit, withdrawal, interest)'
    )
    
    amount = models.DecimalField(
        decimal_places=2,
        max_digits=12,
        help_text='Transaction amount'
    )
    balance_before = models.DecimalField(
        decimal_places=2,
        max_digits=12,
        help_text='Account balance before the transaction'
    )
    balance_after = models.DecimalField(
        decimal_places=2,
        max_digits=12,
        help_text='Account balance after the transaction'
    )
    
    timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text='When the action was performed'
    )
    
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text='IP address of the user who initiated the transaction'
    )
    user_agent = models.TextField(
        null=True,
        blank=True,
        help_text='User agent string for security monitoring'
    )
    
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text='Additional context and metadata for forensic analysis'
    )
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['action_type', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.action_type} - {self.user.email} - {self.timestamp}"
    
    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise ValueError("Audit logs are immutable and cannot be modified")
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        raise ValueError("Audit logs are immutable and cannot be deleted")


def create_audit_log(user, transaction, action_type, balance_before, balance_after, request=None):
    ip_address = None
    user_agent = None
    
    if request:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0].strip()
        else:
            ip_address = request.META.get('REMOTE_ADDR')
        
        user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    audit_log = AuditLog.objects.create(
        user=user,
        transaction=transaction,
        action_type=action_type,
        amount=transaction.amount,
        balance_before=balance_before,
        balance_after=balance_after,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    return audit_log
