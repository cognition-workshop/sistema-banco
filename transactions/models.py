from django.db import models
from django.conf import settings

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
    balance_before_transaction = models.DecimalField(
        decimal_places=2,
        max_digits=12,
        null=True,
        blank=True,
        help_text='Account balance before this transaction'
    )
    transaction_type = models.PositiveSmallIntegerField(
        choices=TRANSACTION_TYPE_CHOICES
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='performed_transactions',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        help_text='User who performed this transaction (null for system operations like interest)'
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text='IP address from which the transaction was initiated'
    )

    def __str__(self):
        return str(self.account.account_no)

    class Meta:
        ordering = ['timestamp']
        permissions = [
            ('cannot_delete_transaction', 'Cannot delete transactions'),
        ]
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['user']),
            models.Index(fields=['account', 'timestamp']),
        ]
    
    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise ValueError(
                'Transaction records are immutable and cannot be modified. '
                'This is required for audit compliance.'
            )
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        raise ValueError(
            'Transaction records cannot be deleted. '
            'This is required for audit compliance.'
        )
