import hashlib
import json
from django.db import models
from django.core.exceptions import ValidationError

from .constants import TRANSACTION_TYPE_CHOICES, DEPOSIT, WITHDRAWAL
from accounts.models import UserBankAccount


class AuditQueryManager(models.Manager):
    """Custom manager for efficient audit queries."""
    
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)
    
    def for_user(self, user):
        """Get all transactions by a specific user."""
        return self.filter(user=user).select_related('account', 'account__user')
    
    def for_account(self, account):
        """Get all transactions for a specific account."""
        return self.filter(account=account).select_related('user')
    
    def by_date_range(self, start_date, end_date):
        """Get transactions within a date range."""
        return self.filter(timestamp__date__range=[start_date, end_date])
    
    def by_type(self, transaction_type):
        """Get transactions of a specific type."""
        return self.filter(transaction_type=transaction_type)
    
    def suspicious_activity(self):
        """Identify potentially suspicious transactions."""
        from django.db.models import Count
        from datetime import timedelta
        from django.utils import timezone
        
        recent_time = timezone.now() - timedelta(hours=24)
        return self.filter(
            transaction_type=WITHDRAWAL,
            timestamp__gte=recent_time
        ).values('account', 'user').annotate(
            withdrawal_count=Count('id')
        ).filter(withdrawal_count__gte=5)
    
    def verify_all_hashes(self):
        """Verify hash integrity for all transactions."""
        invalid_transactions = []
        for transaction in self.all():
            if not transaction.verify_hash_integrity():
                invalid_transactions.append(transaction)
        return invalid_transactions


class Transaction(models.Model):
    account = models.ForeignKey(
        UserBankAccount,
        related_name='transactions',
        on_delete=models.PROTECT,
    )
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.PROTECT,
        related_name='audit_transactions',
        null=True,
        help_text='User who initiated this transaction'
    )
    amount = models.DecimalField(
        decimal_places=2,
        max_digits=12
    )
    previous_balance = models.DecimalField(
        decimal_places=2,
        max_digits=12,
        help_text='Account balance before this transaction'
    )
    balance_after_transaction = models.DecimalField(
        decimal_places=2,
        max_digits=12
    )
    transaction_type = models.PositiveSmallIntegerField(
        choices=TRANSACTION_TYPE_CHOICES
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text='IP address of the user who initiated the transaction'
    )
    previous_hash = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        help_text='SHA-256 hash of the previous transaction (for chain integrity)'
    )
    current_hash = models.CharField(
        max_length=64,
        editable=False,
        help_text='SHA-256 hash of this transaction data'
    )
    is_deleted = models.BooleanField(
        default=False,
        help_text='Soft delete flag - transactions are never actually deleted'
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text='Additional audit metadata (e.g., user agent, request ID)'
    )

    objects = models.Manager()
    audit = AuditQueryManager()

    def __str__(self):
        return str(self.account.account_no)

    class Meta:
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['account', 'timestamp']),
            models.Index(fields=['transaction_type', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]
        permissions = [
            ('view_audit_log', 'Can view audit logs'),
        ]
    
    def calculate_hash(self):
        """Calculate SHA-256 hash of transaction data for integrity verification."""
        hash_data = {
            'account_id': self.account_id,
            'amount': str(self.amount),
            'previous_balance': str(self.previous_balance),
            'balance_after_transaction': str(self.balance_after_transaction),
            'transaction_type': self.transaction_type,
            'timestamp': self.timestamp.isoformat() if self.timestamp else '',
            'user_id': self.user_id if self.user_id else 'SYSTEM',
            'previous_hash': self.previous_hash or '',
        }
        hash_string = json.dumps(hash_data, sort_keys=True)
        return hashlib.sha256(hash_string.encode()).hexdigest()
    
    def get_previous_transaction(self):
        """Get the previous transaction for this account for hash chaining."""
        return Transaction.objects.filter(
            account=self.account,
            timestamp__lt=self.timestamp,
            is_deleted=False
        ).order_by('-timestamp').first()
    
    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise ValidationError(
                "Audit log transactions cannot be modified after creation. "
                "This ensures data integrity for regulatory compliance."
            )
        
        if not self.previous_hash:
            prev_transaction = self.get_previous_transaction()
            if prev_transaction:
                self.previous_hash = prev_transaction.current_hash
        
        if not self.current_hash:
            if not self.timestamp:
                from django.utils import timezone
                self.timestamp = timezone.now()
            self.current_hash = self.calculate_hash()
        
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """Soft delete - mark as deleted but never actually remove from database."""
        if not self.is_deleted:
            self.is_deleted = True
            Transaction.objects.filter(pk=self.pk).update(is_deleted=True)
        return
    
    def verify_hash_integrity(self):
        """Verify this transaction's hash matches its data."""
        expected_hash = self.calculate_hash()
        return self.current_hash == expected_hash
    
    def verify_chain_integrity(self):
        """Verify the hash chain is intact."""
        prev_transaction = self.get_previous_transaction()
        if prev_transaction:
            return self.previous_hash == prev_transaction.current_hash
        return self.previous_hash is None or self.previous_hash == ''
