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
    balance_before_transaction = models.DecimalField(
        decimal_places=2,
        max_digits=12,
        help_text='Account balance before this transaction was applied'
    )
    performed_by = models.ForeignKey(
        'accounts.User',
        related_name='performed_transactions',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_index=True,
        help_text='User who performed this transaction (null for system operations)'
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text='IP address of the user who performed this transaction'
    )
    user_agent = models.TextField(
        null=True,
        blank=True,
        help_text='User agent string from the browser/client'
    )
    operation_source = models.CharField(
        max_length=20,
        choices=[
            ('web', 'Web'),
            ('api', 'API'),
            ('admin', 'Admin'),
            ('system', 'System'),
        ],
        default='web',
        db_index=True,
        help_text='Source of the operation'
    )

    def __str__(self):
        return str(self.account.account_no)

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise ValueError(
                'Transaction records are immutable and cannot be modified after creation. '
                'This is required for audit compliance.'
            )
        
        if self.balance_after_transaction is None:
            raise ValueError('balance_after_transaction must be set before saving')
        if self.balance_before_transaction is None:
            raise ValueError('balance_before_transaction must be set before saving')
        
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        raise ValueError(
            'Transaction records cannot be deleted. '
            'This is required for audit compliance and regulatory requirements.'
        )

    class Meta:
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['timestamp', 'account']),
            models.Index(fields=['transaction_type', 'timestamp']),
        ]
