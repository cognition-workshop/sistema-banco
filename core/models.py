from django.db import models
from accounts.models import User, UserBankAccount
from transactions.models import Transaction


class FraudAlert(models.Model):
    ALERT_TYPES = (
        ('MULTIPLE_TRANSACTIONS', 'Multiple Transactions in Short Period'),
        ('LARGE_WITHDRAWAL', 'Large Withdrawal Alert'),
        ('ABNORMAL_PATTERN', 'Abnormal Transaction Pattern'),
    )
    
    STATUS_CHOICES = (
        ('PENDING', 'Pending Review'),
        ('REVIEWED', 'Reviewed'),
        ('RESOLVED', 'Resolved'),
        ('FALSE_POSITIVE', 'False Positive'),
    )
    
    alert_type = models.CharField(max_length=30, choices=ALERT_TYPES)
    account = models.ForeignKey(UserBankAccount, on_delete=models.CASCADE, related_name='fraud_alerts')
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, null=True, blank=True)
    description = models.TextField()
    severity = models.CharField(max_length=10, choices=[('LOW', 'Low'), ('MEDIUM', 'Medium'), ('HIGH', 'High')])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_alerts')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.alert_type} - {self.account.account_no} ({self.created_at.strftime('%Y-%m-%d')})"
