from django.db import models
from django.utils import timezone


class DailyMetrics(models.Model):
    date = models.DateField(unique=True, default=timezone.now)
    total_transactions = models.IntegerField(default=0)
    total_deposit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_withdrawal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    new_users = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-date']
    
    def __str__(self):
        return f"Metrics for {self.date}"
