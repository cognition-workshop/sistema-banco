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
    balance_before_transaction = models.DecimalField(
        decimal_places=2,
        max_digits=12,
        null=True,
        blank=True,
        help_text='Account balance before this transaction'
    )
    balance_after_transaction = models.DecimalField(
        decimal_places=2,
        max_digits=12
    )
    transaction_type = models.PositiveSmallIntegerField(
        choices=TRANSACTION_TYPE_CHOICES
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='transactions',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_index=True,
        help_text='User who initiated this transaction (null for system-generated transactions like interest)'
    )
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['transaction_type', 'timestamp']),
            models.Index(fields=['account', 'timestamp']),
        ]

    def __str__(self):
        return str(self.account.account_no)

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise ValueError(
                "Audit requirement: Transactions cannot be modified after creation. "
                "This transaction already exists and is immutable."
            )
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError(
            "Audit requirement: Transactions cannot be deleted. "
            "This ensures immutability for regulatory compliance."
        )
