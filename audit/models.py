from django.db import models
from django.contrib.auth import get_user_model
from accounts.models import UserBankAccount
import hashlib
import json

User = get_user_model()


class AuditLog(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        editable=False
    )
    account = models.ForeignKey(
        UserBankAccount,
        on_delete=models.SET_NULL,
        null=True,
        editable=False
    )
    
    transaction_type = models.CharField(max_length=50, editable=False)
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        editable=False
    )
    balance_before = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        editable=False
    )
    balance_after = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        editable=False
    )
    
    previous_hash = models.CharField(max_length=64, editable=False)
    current_hash = models.CharField(max_length=64, unique=True, editable=False)
    
    ip_address = models.GenericIPAddressField(editable=False)
    user_agent = models.TextField(editable=False)
    additional_data = models.JSONField(default=dict, editable=False)
    
    class Meta:
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['account']),
            models.Index(fields=['current_hash']),
        ]

    def __str__(self):
        return f"Audit #{self.id} - {self.transaction_type} - {self.timestamp}"

    def save(self, *args, **kwargs):
        if not self.current_hash:
            last_audit = AuditLog.objects.order_by('-id').first()
            self.previous_hash = last_audit.current_hash if last_audit else '0' * 64
            
            self.current_hash = self.generate_hash()
        
        super().save(*args, **kwargs)

    def generate_hash(self):
        """Generate SHA-256 hash of audit log data"""
        data = {
            'timestamp': str(self.timestamp),
            'user_id': self.user_id,
            'account_id': self.account_id,
            'transaction_type': self.transaction_type,
            'amount': str(self.amount),
            'balance_before': str(self.balance_before),
            'balance_after': str(self.balance_after),
            'previous_hash': self.previous_hash,
            'ip_address': self.ip_address,
        }
        data_string = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_string.encode()).hexdigest()

    @classmethod
    def verify_chain_integrity(cls):
        """Verify the integrity of the entire audit log chain"""
        audit_logs = cls.objects.order_by('id')
        previous_hash = '0' * 64
        
        for log in audit_logs:
            if log.previous_hash != previous_hash:
                return False, f"Chain broken at log #{log.id}"
            
            expected_hash = log.generate_hash()
            if log.current_hash != expected_hash:
                return False, f"Hash mismatch at log #{log.id}"
            
            previous_hash = log.current_hash
        
        return True, "Chain integrity verified"
