from django.db import models

from .constants import TRANSACTION_TYPE_CHOICES, AUDIT_ACTION_CHOICES
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
        related_name='audit_logs',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text='User who performed the action. Null for system actions.'
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text='IP address of the request origin'
    )
    user_agent = models.TextField(
        null=True,
        blank=True,
        help_text='Browser/device information'
    )
    action_type = models.CharField(
        max_length=50,
        choices=AUDIT_ACTION_CHOICES
    )
    success = models.BooleanField(default=True)
    error_message = models.TextField(
        null=True,
        blank=True,
        help_text='Error message if action failed'
    )
    transaction = models.ForeignKey(
        Transaction,
        related_name='audit_logs',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text='Related transaction if applicable'
    )
    amount = models.DecimalField(
        decimal_places=2,
        max_digits=12,
        null=True,
        blank=True,
        help_text='Amount involved in the action'
    )
    additional_data = models.JSONField(
        default=dict,
        blank=True,
        help_text='Additional metadata in JSON format'
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.action_type} - {self.timestamp}"

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['action_type', '-timestamp']),
        ]
