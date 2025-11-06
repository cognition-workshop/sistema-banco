from django.db import models
import hashlib
import json

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
    user_agent = models.TextField(null=True, blank=True)
    geolocation = models.JSONField(null=True, blank=True)
    hash_signature = models.CharField(max_length=64, blank=True)

    def generate_hash(self):
        """Generate SHA-256 hash signature for transaction immutability."""
        data = {
            'account_id': self.account.id,
            'amount': str(self.amount),
            'balance_after_transaction': str(self.balance_after_transaction),
            'transaction_type': self.transaction_type,
            'timestamp': self.timestamp.isoformat() if self.timestamp else '',
            'ip_address': self.ip_address or '',
        }
        hash_string = json.dumps(data, sort_keys=True)
        return hashlib.sha256(hash_string.encode()).hexdigest()
    
    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise Exception('Transactions cannot be modified (BACEN compliance).')
        
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new and not self.hash_signature:
            self.hash_signature = self.generate_hash()
            super().save(update_fields=['hash_signature'])
    
    def delete(self, *args, **kwargs):
        raise Exception('Transactions cannot be deleted (BACEN compliance).')

    def __str__(self):
        return str(self.account.get_formatted_account())

    class Meta:
        ordering = ['timestamp']
