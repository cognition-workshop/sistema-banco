from django.db import models
from django.conf import settings
from accounts.models import UserBankAccount


class FraudRule(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    rule_type = models.CharField(max_length=50, choices=[
        ('HIGH_VALUE', 'High Value Transaction'),
        ('HIGH_FREQUENCY', 'High Frequency'),
        ('SUSPICIOUS_TIMING', 'Suspicious Timing'),
    ])
    threshold_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    time_window_minutes = models.IntegerField(null=True, blank=True)
    max_transactions = models.IntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name


class FraudAlert(models.Model):
    account = models.ForeignKey(UserBankAccount, on_delete=models.CASCADE, related_name='fraud_alerts')
    rule = models.ForeignKey(FraudRule, on_delete=models.CASCADE)
    severity = models.CharField(max_length=20, choices=[
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ], default='MEDIUM')
    description = models.TextField()
    status = models.CharField(max_length=20, choices=[
        ('PENDING', 'Pending'),
        ('INVESTIGATING', 'Investigating'),
        ('RESOLVED', 'Resolved'),
        ('FALSE_POSITIVE', 'False Positive'),
    ], default='PENDING')
    investigated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='investigated_alerts'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"Alert for {self.account.account_no} - {self.severity}"
    
    class Meta:
        ordering = ['-created_at']


class AdminAuditLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    action = models.CharField(max_length=255)
    target_model = models.CharField(max_length=100, blank=True)
    target_id = models.IntegerField(null=True, blank=True)
    changes = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.email} - {self.action} at {self.timestamp}"
    
    class Meta:
        ordering = ['-timestamp']


class AccountWhitelist(models.Model):
    account = models.OneToOneField(UserBankAccount, on_delete=models.CASCADE)
    reason = models.TextField()
    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Whitelisted: {self.account.account_no}"
