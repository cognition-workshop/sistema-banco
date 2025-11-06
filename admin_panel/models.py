from django.db import models
from django.contrib.auth import get_user_model
from accounts.models import UserBankAccount
from transactions.models import Transaction

User = get_user_model()


class AdminUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='admin_profile')
    is_super_admin = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Admin: {self.user.email}"
    
    class Meta:
        verbose_name = 'Admin User'
        verbose_name_plural = 'Admin Users'


class AdminPermission(models.Model):
    admin_user = models.ForeignKey(AdminUser, on_delete=models.CASCADE, related_name='permissions')
    permission_name = models.CharField(max_length=100)
    granted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['admin_user', 'permission_name']
        verbose_name = 'Admin Permission'
        verbose_name_plural = 'Admin Permissions'
    
    def __str__(self):
        return f"{self.admin_user.user.email} - {self.permission_name}"


class FraudDetectionRule(models.Model):
    RULE_TYPE_CHOICES = [
        ('amount_threshold', 'Amount Threshold'),
        ('frequency', 'Frequency'),
        ('velocity', 'Velocity'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField()
    rule_type = models.CharField(max_length=50, choices=RULE_TYPE_CHOICES)
    threshold_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    time_window_minutes = models.IntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(AdminUser, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        verbose_name = 'Fraud Detection Rule'
        verbose_name_plural = 'Fraud Detection Rules'
    
    def __str__(self):
        return f"{self.name} ({self.rule_type})"


class FraudAlert(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('investigating', 'Investigating'),
        ('resolved', 'Resolved'),
        ('false_positive', 'False Positive'),
    ]
    
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='fraud_alerts')
    rule = models.ForeignKey(FraudDetectionRule, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    details = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(AdminUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_alerts')
    
    class Meta:
        verbose_name = 'Fraud Alert'
        verbose_name_plural = 'Fraud Alerts'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Alert #{self.id} - {self.status}"
