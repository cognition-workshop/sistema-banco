from django.db import models
from django.contrib.auth import get_user_model
from accounts.models import UserBankAccount
from transactions.models import Transaction

User = get_user_model()


class AnalyticsReport(models.Model):
    REPORT_TYPE_CHOICES = [
        ('monthly', 'Relatório Mensal'),
        ('quarterly', 'Relatório Trimestral'),
        ('annual', 'Relatório Anual'),
        ('custom', 'Relatório Customizado'),
    ]
    
    title = models.CharField(max_length=200)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    data = models.JSONField(default=dict)
    
    class Meta:
        ordering = ['-generated_at']
        
    def __str__(self):
        return f"{self.title} - {self.generated_at.strftime('%Y-%m-%d')}"


class UserActivity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    activity_date = models.DateField(auto_now_add=True)
    login_count = models.IntegerField(default=0)
    transaction_count = models.IntegerField(default=0)
    total_deposits = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_withdrawals = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    class Meta:
        ordering = ['-activity_date']
        unique_together = ['user', 'activity_date']
        
    def __str__(self):
        return f"{self.user.email} - {self.activity_date}"
