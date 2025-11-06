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
        null=True,
        blank=True,
        help_text='User who initiated the transaction (null for system operations)'
    )
    account = models.ForeignKey(
        UserBankAccount,
        related_name='audit_logs',
        on_delete=models.PROTECT,
    )
    transaction = models.ForeignKey(
        Transaction,
        related_name='audit_logs',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    operation_type = models.PositiveSmallIntegerField(
        choices=TRANSACTION_TYPE_CHOICES
    )
    amount = models.DecimalField(
        decimal_places=2,
        max_digits=12
    )
    balance_before = models.DecimalField(
        decimal_places=2,
        max_digits=12
    )
    balance_after = models.DecimalField(
        decimal_places=2,
        max_digits=12
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    description = models.TextField(blank=True, default='')

    def __str__(self):
        return f'{self.get_operation_type_display()} - {self.account.account_no} - {self.timestamp}'

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
