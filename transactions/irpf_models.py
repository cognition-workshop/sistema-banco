from django.db import models
from accounts.models import User


class IRPFReport(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='irpf_reports')
    year = models.IntegerField()
    total_deposits = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_withdrawals = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_interest = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    opening_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    closing_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    transaction_count = models.IntegerField(default=0)
    generated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'year']
        ordering = ['-year', '-generated_at']
    
    def __str__(self):
        return f"IRPF {self.year} - {self.user.email}"
