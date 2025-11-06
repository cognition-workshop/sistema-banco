from django.db import models
from django.conf import settings
from accounts.models import UserBankAccount
from transactions.models import Transaction


class FraudAlert(models.Model):
    SEVERITY_LOW = 'LOW'
    SEVERITY_MEDIUM = 'MEDIUM'
    SEVERITY_HIGH = 'HIGH'
    SEVERITY_CRITICAL = 'CRITICAL'
    
    SEVERITY_CHOICES = [
        (SEVERITY_LOW, 'Baixa'),
        (SEVERITY_MEDIUM, 'Média'),
        (SEVERITY_HIGH, 'Alta'),
        (SEVERITY_CRITICAL, 'Crítica'),
    ]
    
    STATUS_PENDING = 'PENDING'
    STATUS_INVESTIGATING = 'INVESTIGATING'
    STATUS_RESOLVED = 'RESOLVED'
    STATUS_FALSE_POSITIVE = 'FALSE_POSITIVE'
    
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pendente'),
        (STATUS_INVESTIGATING, 'Em Investigação'),
        (STATUS_RESOLVED, 'Resolvido'),
        (STATUS_FALSE_POSITIVE, 'Falso Positivo'),
    ]
    
    account = models.ForeignKey(
        UserBankAccount,
        on_delete=models.CASCADE,
        related_name='fraud_alerts'
    )
    transaction = models.ForeignKey(
        Transaction,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='fraud_alerts'
    )
    alert_type = models.CharField(max_length=100)
    description = models.TextField()
    severity = models.CharField(
        max_length=20,
        choices=SEVERITY_CHOICES,
        default=SEVERITY_MEDIUM
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING
    )
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_fraud_alerts'
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Alerta de Fraude'
        verbose_name_plural = 'Alertas de Fraude'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['status', 'severity']),
        ]
    
    def __str__(self):
        return f'Alerta #{self.id} - {self.account.account_no} ({self.get_severity_display()})'
    
    def is_critical(self):
        return self.severity == self.SEVERITY_CRITICAL
    
    def is_pending(self):
        return self.status == self.STATUS_PENDING
