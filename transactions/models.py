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

    def __str__(self):
        return str(self.account.account_no)

    class Meta:
        ordering = ['timestamp']


class AuditLog(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    transaction_type = models.PositiveSmallIntegerField(
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
    account = models.ForeignKey(
        UserBankAccount,
        related_name='audit_logs',
        on_delete=models.PROTECT,
    )
    previous_hash = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        help_text='Hash of the previous audit log entry for this account'
    )
    current_hash = models.CharField(
        max_length=64,
        unique=True,
        help_text='SHA-256 hash of this audit log entry'
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text='Additional metadata: IP address, user agent, source, etc.'
    )
    transaction = models.OneToOneField(
        Transaction,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='audit_log'
    )

    class Meta:
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['account', '-timestamp']),
        ]

    def __str__(self):
        return f"AuditLog {self.id} - {self.account.account_no} - {self.get_transaction_type_display()}"

    def _calculate_hash(self):
        hash_data = {
            'account_id': self.account_id,
            'transaction_type': self.transaction_type,
            'amount': str(self.amount),
            'balance_before': str(self.balance_before),
            'balance_after': str(self.balance_after),
            'previous_hash': self.previous_hash or '',
        }
        hash_string = json.dumps(hash_data, sort_keys=True)
        return hashlib.sha256(hash_string.encode()).hexdigest()

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise ValueError("AuditLog entries cannot be modified after creation (BACEN compliance)")
        
        if not self.current_hash:
            self.current_hash = self._calculate_hash()
        
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError("AuditLog entries cannot be deleted (BACEN compliance)")


def create_audit_log(account, transaction_type, amount, balance_before, balance_after, 
                     transaction=None, metadata=None):
    previous_log = AuditLog.objects.filter(account=account).order_by('-timestamp').first()
    previous_hash = previous_log.current_hash if previous_log else None
    
    audit_log = AuditLog(
        account=account,
        transaction_type=transaction_type,
        amount=amount,
        balance_before=balance_before,
        balance_after=balance_after,
        transaction=transaction,
        previous_hash=previous_hash,
        metadata=metadata or {}
    )
    audit_log.save()
    return audit_log
