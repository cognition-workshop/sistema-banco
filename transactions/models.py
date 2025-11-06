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
    
    ACTION_CHOICES = [
        (DEPOSIT, 'Deposit'),
        (WITHDRAWAL, 'Withdrawal'),
        (INTEREST, 'Interest'),
    ]
    
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.PROTECT,
        related_name='audit_logs',
        help_text='User who performed the action'
    )
    account = models.ForeignKey(
        'accounts.UserBankAccount',
        on_delete=models.PROTECT,
        related_name='audit_logs',
        help_text='Account affected by the action'
    )
    transaction = models.ForeignKey(
        Transaction,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='audit_logs',
        help_text='Related transaction if applicable'
    )
    action_type = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        help_text='Type of balance-changing operation'
    )
    amount = models.DecimalField(
        decimal_places=2,
        max_digits=12,
        help_text='Transaction amount'
    )
    balance_before = models.DecimalField(
        decimal_places=2,
        max_digits=12,
        help_text='Account balance before the operation'
    )
    balance_after = models.DecimalField(
        decimal_places=2,
        max_digits=12,
        help_text='Account balance after the operation'
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text='When the operation occurred'
    )
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['account', '-timestamp']),
            models.Index(fields=['action_type', '-timestamp']),
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
        return f'{self.action_type} - {self.account.account_no} - {self.timestamp}'
