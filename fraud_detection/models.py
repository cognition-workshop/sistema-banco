from django.db import models
from django.contrib.auth import get_user_model
from transactions.models import Transaction
from accounts.models import UserBankAccount

User = get_user_model()

RULE_TYPE_CHOICES = (
    ('high_amount', 'High Amount'),
    ('frequency', 'High Frequency'),
    ('velocity', 'High Velocity'),
    ('unusual_time', 'Unusual Time'),
)

SEVERITY_CHOICES = (
    ('low', 'Low'),
    ('medium', 'Medium'),
    ('high', 'High'),
    ('critical', 'Critical'),
)

STATUS_CHOICES = (
    ('pending', 'Pending'),
    ('investigating', 'Investigating'),
    ('resolved', 'Resolved'),
    ('false_positive', 'False Positive'),
)


class FraudRule(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    rule_type = models.CharField(max_length=20, choices=RULE_TYPE_CHOICES)
    threshold_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Threshold amount for high_amount rules'
    )
    time_window_minutes = models.IntegerField(
        null=True,
        blank=True,
        help_text='Time window in minutes for frequency/velocity analysis'
    )
    max_transactions = models.IntegerField(
        null=True,
        blank=True,
        help_text='Maximum number of transactions allowed in time window'
    )
    is_active = models.BooleanField(default=True)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='medium')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.get_severity_display()})"

    class Meta:
        ordering = ['-created_at']


class FraudAlert(models.Model):
    STATUS_CHOICES = STATUS_CHOICES
    SEVERITY_CHOICES = SEVERITY_CHOICES
    
    transaction = models.ForeignKey(
        Transaction,
        related_name='fraud_alerts',
        on_delete=models.CASCADE
    )
    rule = models.ForeignKey(
        FraudRule,
        related_name='alerts',
        on_delete=models.CASCADE
    )
    account = models.ForeignKey(
        UserBankAccount,
        related_name='fraud_alerts',
        on_delete=models.CASCADE
    )
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    description = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='resolved_alerts'
    )
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Alert #{self.id} - {self.rule.name} - {self.get_status_display()}"

    class Meta:
        ordering = ['-created_at']
