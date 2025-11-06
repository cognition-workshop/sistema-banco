from django.db import models

from .constants import TRANSACTION_TYPE_CHOICES
from accounts.models import UserBankAccount
from django.conf import settings


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
        related_name='audit_logs',
        on_delete=models.PROTECT,
        help_text='User who performed the operation'
    )
    account = models.ForeignKey(
        UserBankAccount,
        related_name='audit_logs',
        on_delete=models.PROTECT,
        help_text='Account affected by the operation'
    )
    transaction = models.ForeignKey(
        Transaction,
        related_name='audit_logs',
        on_delete=models.PROTECT,
        null=True,
        help_text='Related transaction record'
    )
    operation_type = models.PositiveSmallIntegerField(
        choices=TRANSACTION_TYPE_CHOICES,
        help_text='Type of operation: deposit, withdrawal, or interest'
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
    description = models.TextField(
        blank=True,
        help_text='Additional context or notes about the operation'
    )

    def __str__(self):
        return f"{self.get_operation_type_display()} - {self.account.account_no} - {self.timestamp}"

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
