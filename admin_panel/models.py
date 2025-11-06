from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

from .constants import (
    ADMIN_ROLE_CHOICES, SENIOR_ADMIN,
    AUDIT_ACTION_CHOICES,
    FRAUD_RULE_CHOICES,
    ALERT_STATUS_CHOICES, ALERT_PENDING,
    HEALTH_METRIC_CHOICES,
    SEVERITY_CHOICES, SEVERITY_MEDIUM
)

User = get_user_model()


class AdminUser(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='admin_user'
    )
    role = models.CharField(
        max_length=20,
        choices=ADMIN_ROLE_CHOICES,
        default=SENIOR_ADMIN
    )
    is_admin_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'admin_panel_admin_user'
        
    def __str__(self):
        return f"{self.user.email} ({self.get_role_display()})"


class AuditLog(models.Model):
    admin_user = models.ForeignKey(
        AdminUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_logs'
    )
    action_type = models.CharField(
        max_length=20,
        choices=AUDIT_ACTION_CHOICES
    )
    target_model = models.CharField(max_length=100)
    target_id = models.IntegerField(null=True, blank=True)
    details = models.JSONField(default=dict)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        db_table = 'admin_panel_audit_log'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['admin_user', '-timestamp']),
            models.Index(fields=['target_model', 'target_id']),
        ]
        
    def __str__(self):
        return f"{self.admin_user} - {self.action_type} - {self.target_model}"


class FraudRule(models.Model):
    name = models.CharField(max_length=200)
    rule_type = models.CharField(
        max_length=50,
        choices=FRAUD_RULE_CHOICES
    )
    parameters = models.JSONField(
        default=dict,
        help_text="Rule-specific parameters as JSON"
    )
    is_active = models.BooleanField(default=True)
    severity = models.CharField(
        max_length=20,
        choices=SEVERITY_CHOICES,
        default=SEVERITY_MEDIUM
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        AdminUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_fraud_rules'
    )
    
    class Meta:
        db_table = 'admin_panel_fraud_rule'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.name} ({self.get_rule_type_display()})"


class FraudAlert(models.Model):
    transaction = models.ForeignKey(
        'transactions.Transaction',
        on_delete=models.CASCADE,
        related_name='fraud_alerts'
    )
    rule = models.ForeignKey(
        FraudRule,
        on_delete=models.CASCADE,
        related_name='alerts'
    )
    detected_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=ALERT_STATUS_CHOICES,
        default=ALERT_PENDING
    )
    reviewed_by = models.ForeignKey(
        AdminUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_alerts'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'admin_panel_fraud_alert'
        ordering = ['-detected_at']
        indexes = [
            models.Index(fields=['-detected_at']),
            models.Index(fields=['status', '-detected_at']),
            models.Index(fields=['transaction']),
        ]
        
    def __str__(self):
        return f"Alert #{self.id} - {self.rule.name} - {self.status}"


class SystemHealthMetric(models.Model):
    metric_type = models.CharField(
        max_length=50,
        choices=HEALTH_METRIC_CHOICES
    )
    value = models.FloatField()
    details = models.JSONField(default=dict)
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('HEALTHY', 'Healthy'),
            ('WARNING', 'Warning'),
            ('CRITICAL', 'Critical'),
        ],
        default='HEALTHY'
    )
    
    class Meta:
        db_table = 'admin_panel_system_health_metric'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['metric_type', '-timestamp']),
        ]
        
    def __str__(self):
        return f"{self.get_metric_type_display()} - {self.value} - {self.status}"
