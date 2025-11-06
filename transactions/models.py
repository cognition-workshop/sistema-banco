import hashlib
from django.db import models
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
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    geolocation = models.CharField(max_length=255, null=True, blank=True)
    channel = models.CharField(max_length=50, null=True, blank=True)
    hash_signature = models.CharField(max_length=64, editable=False, null=True, blank=True)

    def __str__(self):
        return str(self.account.account_no)

    def _generate_hash(self):
        data = f"{self.account_id}{self.amount}{self.transaction_type}{self.timestamp}"
        return hashlib.sha256(data.encode()).hexdigest()

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise ValidationError("Cannot modify existing transactions. Transactions are immutable.")
        
        if not self.hash_signature:
            self.hash_signature = self._generate_hash()
        
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Cannot delete transactions. Transactions are immutable.")

    class Meta:
        ordering = ['timestamp']


class FailedTransaction(models.Model):
    account = models.ForeignKey(
        UserBankAccount,
        related_name='failed_transactions',
        on_delete=models.CASCADE,
    )
    amount = models.DecimalField(
        decimal_places=2,
        max_digits=12
    )
    transaction_type = models.PositiveSmallIntegerField(
        choices=TRANSACTION_TYPE_CHOICES
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    geolocation = models.CharField(max_length=255, null=True, blank=True)
    channel = models.CharField(max_length=50, null=True, blank=True)
    error_message = models.TextField()
    error_code = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return f"Failed transaction for {self.account.account_no} at {self.timestamp}"

    class Meta:
        ordering = ['-timestamp']
