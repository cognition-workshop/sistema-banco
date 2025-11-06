from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

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
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text='User who performed the operation (null for system operations)'
    )
    account = models.ForeignKey(
        UserBankAccount,
        related_name='audit_logs',
        on_delete=models.CASCADE,
        help_text='Account affected by the operation'
    )
    operation_type = models.PositiveSmallIntegerField(
        choices=TRANSACTION_TYPE_CHOICES,
        help_text='Type of operation performed'
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
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text='IP address of the user (if applicable)'
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text='Additional metadata about the operation'
    )

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['account', '-timestamp']),
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['operation_type', '-timestamp']),
        ]

    def __str__(self):
        operation_name = dict(TRANSACTION_TYPE_CHOICES).get(self.operation_type, 'Unknown')
        return f"{operation_name} - {self.account.account_no} - {self.timestamp}"

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise ValidationError("Audit logs cannot be modified after creation")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Audit logs cannot be deleted")
