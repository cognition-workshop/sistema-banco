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
    DEPOSIT = 'DEPOSIT'
    WITHDRAWAL = 'WITHDRAWAL'
    INTEREST = 'INTEREST'
    
    ACTION_CHOICES = (
        (DEPOSIT, 'Deposit'),
        (WITHDRAWAL, 'Withdrawal'),
        (INTEREST, 'Interest Calculation'),
    )
    
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        help_text='User who initiated the action (null for system operations)'
    )
    account = models.ForeignKey(
        'accounts.UserBankAccount',
        related_name='audit_logs',
        on_delete=models.PROTECT,
    )
    action_type = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
    )
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    balance_before = models.DecimalField(
        decimal_places=2,
        max_digits=12,
    )
    balance_after = models.DecimalField(
        decimal_places=2,
        max_digits=12,
    )
    amount = models.DecimalField(
        decimal_places=2,
        max_digits=12,
    )
    transaction = models.ForeignKey(
        Transaction,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        help_text='Related transaction record if applicable'
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=512, null=True, blank=True)
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text='Additional context for the operation'
    )
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['account', '-timestamp']),
            models.Index(fields=['action_type', '-timestamp']),
            models.Index(fields=['user', '-timestamp']),
        ]
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
    
    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise ValueError('Audit logs cannot be modified after creation')
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        raise ValueError('Audit logs cannot be deleted')
    
    def __str__(self):
        return f"{self.action_type} - Account {self.account.account_no} - {self.timestamp}"


def create_audit_log(account, action_type, amount, balance_before, balance_after, 
                     user=None, transaction=None, request=None, metadata=None):
    audit_data = {
        'account': account,
        'action_type': action_type,
        'amount': amount,
        'balance_before': balance_before,
        'balance_after': balance_after,
        'user': user,
        'transaction': transaction,
        'metadata': metadata or {},
    }
    
    if request:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            audit_data['ip_address'] = x_forwarded_for.split(',')[0]
        else:
            audit_data['ip_address'] = request.META.get('REMOTE_ADDR')
        
        audit_data['user_agent'] = request.META.get('HTTP_USER_AGENT', '')[:512]
    
    return AuditLog.objects.create(**audit_data)
