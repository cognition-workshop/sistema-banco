from django.db import models
from accounts.models import UserBankAccount


class AnnualTaxReport(models.Model):
    account = models.ForeignKey(
        UserBankAccount,
        related_name='tax_reports',
        on_delete=models.CASCADE
    )
    year = models.IntegerField()
    
    total_deposits = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_withdrawals = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_interest = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_pix_received = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_pix_sent = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    opening_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    closing_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    generated_at = models.DateTimeField(auto_now_add=True)
    pdf_file = models.FileField(upload_to='tax_reports/', blank=True)

    class Meta:
        unique_together = [['account', 'year']]
        ordering = ['-year']

    def __str__(self):
        return f"Tax Report {self.year} - {self.account}"
