import hashlib
from django.db import models
from django.utils import timezone

from .constants import TRANSACTION_TYPE_CHOICES
from accounts.models import UserBankAccount


class Transaction(models.Model):
    account = models.ForeignKey(
        UserBankAccount,
        related_name='transactions',
        on_delete=models.CASCADE,
    )
    amount = models.DecimalField(
        decimal_places=2,
        max_digits=12
    )
    balance_after_transaction = models.DecimalField(
        decimal_places=2,
        max_digits=12
    )
    transaction_type = models.PositiveSmallIntegerField(
        choices=TRANSACTION_TYPE_CHOICES
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    
    ip_address = models.GenericIPAddressField(null=True, blank=True, help_text='IP de origem da transação')
    user_agent = models.CharField(max_length=255, blank=True, help_text='User agent do navegador')
    integrity_hash = models.CharField(max_length=64, editable=False, help_text='Hash SHA-256 para integridade')

    def __str__(self):
        return str(self.account.account_no)

    class Meta:
        ordering = ['timestamp']
    
    def save(self, *args, **kwargs):
        if not self.pk:
            hash_string = f"{self.account_id}{self.amount}{self.transaction_type}{timezone.now().isoformat()}"
            self.integrity_hash = hashlib.sha256(hash_string.encode()).hexdigest()
        
        if self.pk:
            raise ValueError("Transações não podem ser editadas após criação (BACEN compliance)")
        
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        raise ValueError("Transações não podem ser deletadas (BACEN compliance)")
