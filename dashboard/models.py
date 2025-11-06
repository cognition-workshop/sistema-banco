from django.db import models
from django.contrib.auth import get_user_model
from accounts.models import UserBankAccount
from transactions.models import Transaction

User = get_user_model()


class DashboardMetric(models.Model):
    metric_date = models.DateField(auto_now_add=True)
    total_users = models.IntegerField(default=0)
    total_transactions = models.IntegerField(default=0)
    total_volume = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_deposits = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_withdrawals = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_interest = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    class Meta:
        ordering = ['-metric_date']
        
    def __str__(self):
        return f"Metrics for {self.metric_date}"
