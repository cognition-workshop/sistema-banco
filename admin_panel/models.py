from django.db import models
from django.contrib.auth import get_user_model
from transactions.models import Transaction

User = get_user_model()


class FraudAlert(models.Model):
    PENDING = 'pending'
    REVIEWED = 'reviewed'
    FALSE_POSITIVE = 'false_positive'
    CONFIRMED_FRAUD = 'confirmed_fraud'
    
    STATUS_CHOICES = [
        (PENDING, 'Pending Review'),
        (REVIEWED, 'Reviewed'),
        (FALSE_POSITIVE, 'False Positive'),
        (CONFIRMED_FRAUD, 'Confirmed Fraud'),
    ]
    
    transaction = models.ForeignKey(
        Transaction,
        on_delete=models.CASCADE,
        related_name='fraud_alerts'
    )
    rule_triggered = models.CharField(max_length=100)
    severity = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    details = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_alerts'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Alert #{self.id} - {self.rule_triggered}"


class SystemHealthLog(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    celery_workers_active = models.IntegerField()
    redis_connected = models.BooleanField()
    redis_memory_usage = models.CharField(max_length=50)
    database_size = models.CharField(max_length=50)
    cpu_usage = models.FloatField()
    memory_usage = models.FloatField()
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"Health Log - {self.timestamp}"
