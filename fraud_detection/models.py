from django.db import models
from accounts.models import UserBankAccount
from transactions.models import Transaction


class FraudAlert(models.Model):
    SEVERITY_CHOICES = [
        ('low', 'Baixa'),
        ('medium', 'Média'),
        ('high', 'Alta'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('investigating', 'Em Investigação'),
        ('resolved', 'Resolvido'),
        ('false_positive', 'Falso Positivo'),
    ]
    
    account = models.ForeignKey(UserBankAccount, on_delete=models.CASCADE, related_name='fraud_alerts')
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, null=True, blank=True)
    alert_type = models.CharField(max_length=50)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.alert_type} - {self.account.account_no} - {self.severity}"
