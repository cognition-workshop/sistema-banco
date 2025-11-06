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
    ACTION_CHOICES = TRANSACTION_TYPE_CHOICES
    
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.PROTECT,
        related_name='audit_logs',
        null=True,
        blank=True,
    )
    account = models.ForeignKey(
        UserBankAccount,
        on_delete=models.PROTECT,
        related_name='audit_logs',
    )
    action_type = models.PositiveSmallIntegerField(
        choices=ACTION_CHOICES,
    )
    
    amount = models.DecimalField(
        decimal_places=2,
        max_digits=12,
    )
    balance_before = models.DecimalField(
        decimal_places=2,
        max_digits=12,
    )
    balance_after = models.DecimalField(
        decimal_places=2,
        max_digits=12,
    )
    
    timestamp = models.DateTimeField(
        auto_now_add=True,
    )
    
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
    )
    user_agent = models.TextField(
        null=True,
        blank=True,
    )
    
    metadata = models.JSONField(
        null=True,
        blank=True,
    )
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['account', 'timestamp']),
            models.Index(fields=['action_type', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
    
    def __str__(self):
        return f"{self.get_action_type_display()} - {self.account.account_no} - {self.timestamp}"
    
    def save(self, force_insert=False, *args, **kwargs):
        if not force_insert and self.pk is not None:
            raise ValueError("AuditLog entries cannot be modified after creation")
        super().save(force_insert=force_insert, *args, **kwargs)
    
    def delete(self, *args, **kwargs):
        raise ValueError("AuditLog entries cannot be deleted")


def create_audit_log(account, action_type, amount, balance_before, balance_after, user=None, request=None, metadata=None):
    ip_address = None
    user_agent = None
    
    if request:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0].strip()
        else:
            ip_address = request.META.get('REMOTE_ADDR')
        
        user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    return AuditLog.objects.create(
        user=user,
        account=account,
        action_type=action_type,
        amount=amount,
        balance_before=balance_before,
        balance_after=balance_after,
        ip_address=ip_address,
        user_agent=user_agent,
        metadata=metadata
    )
