from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.utils import timezone
import hashlib
import json

User = get_user_model()


class AuditLog(models.Model):
    ACTION_CHOICES = (
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('VIEW', 'View'),
    )
    
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_logs'
    )
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=255)
    object_id = models.PositiveIntegerField()
    previous_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    hash_signature = models.CharField(max_length=64, unique=True)
    previous_hash = models.CharField(max_length=64, blank=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['model_name', 'object_id']),
            models.Index(fields=['user', 'timestamp']),
        ]

    def save(self, *args, **kwargs):
        if not self.hash_signature:
            last_log = AuditLog.objects.order_by('-timestamp').first()
            self.previous_hash = last_log.hash_signature if last_log else ''
            
            hash_content = f"{self.timestamp}{self.user_id}{self.action}{self.model_name}{self.object_id}{self.previous_hash}"
            self.hash_signature = hashlib.sha256(hash_content.encode()).hexdigest()
        
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise PermissionDenied("Audit logs cannot be deleted")

    def __str__(self):
        return f"{self.action} on {self.model_name}({self.object_id}) at {self.timestamp}"


class ImmutableTransaction(models.Model):
    transaction_id = models.PositiveIntegerField(db_index=True)
    account_id = models.PositiveIntegerField()
    amount = models.DecimalField(decimal_places=2, max_digits=12)
    balance_after_transaction = models.DecimalField(decimal_places=2, max_digits=12)
    transaction_type = models.PositiveSmallIntegerField()
    timestamp = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    hash_signature = models.CharField(max_length=64, unique=True)
    previous_hash = models.CharField(max_length=64, blank=True)
    digital_signature = models.TextField()

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['account_id', 'timestamp']),
        ]

    def save(self, *args, **kwargs):
        if not self.hash_signature:
            last_transaction = ImmutableTransaction.objects.order_by('-created_at').first()
            self.previous_hash = last_transaction.hash_signature if last_transaction else ''
            
            hash_content = f"{self.transaction_id}{self.account_id}{self.amount}{self.transaction_type}{self.timestamp}{self.previous_hash}"
            self.hash_signature = hashlib.sha256(hash_content.encode()).hexdigest()
            self.digital_signature = self.hash_signature
        
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise PermissionDenied("Immutable transactions cannot be deleted")

    def __str__(self):
        return f"Immutable Transaction {self.transaction_id} at {self.timestamp}"
