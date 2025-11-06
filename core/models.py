from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class AuditLog(models.Model):
    """Immutable audit log for BACEN compliance."""
    
    ACTION_CHOICES = [
        ('CREATE_USER', 'Create User'),
        ('CREATE_ACCOUNT', 'Create Account'),
        ('DEPOSIT', 'Deposit'),
        ('WITHDRAW', 'Withdraw'),
        ('PIX_REGISTER_KEY', 'PIX Register Key'),
        ('PIX_TRANSFER', 'PIX Transfer'),
        ('PIX_GENERATE_QR', 'PIX Generate QR Code'),
        ('INTEREST_CALC', 'Interest Calculation'),
    ]
    
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    resource_type = models.CharField(max_length=50)
    resource_id = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    details = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['user', 'action']),
        ]
    
    def __str__(self):
        return f"{self.timestamp} - {self.action} by {self.user}"
    
    def save(self, *args, **kwargs):
        """Only allow creation, not updates."""
        if self.pk:
            raise ValueError("AuditLog entries cannot be modified")
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """Prevent deletion."""
        raise ValueError("AuditLog entries cannot be deleted")
