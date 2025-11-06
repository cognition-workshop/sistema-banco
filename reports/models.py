from django.db import models
from accounts.models import UserBankAccount


class IRPFReport(models.Model):
    """IRPF (Income Tax) Annual Report."""
    account = models.ForeignKey(
        UserBankAccount,
        related_name='irpf_reports',
        on_delete=models.CASCADE
    )
    year = models.IntegerField()
    total_interest_earned = models.DecimalField(
        decimal_places=2,
        max_digits=12,
        default=0
    )
    report_file = models.FileField(upload_to='irpf_reports/', blank=True)
    csv_file = models.FileField(upload_to='irpf_reports/', blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('account', 'year')
        ordering = ['-year']
    
    def __str__(self):
        return f"IRPF {self.year} - {self.account}"
