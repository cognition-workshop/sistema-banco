import uuid
from django.db import models
from accounts.models import UserBankAccount

from .constants import PIX_KEY_TYPE_CHOICES, PIX_STATUS_CHOICES, PIX_COMPLETED


class PixKey(models.Model):
    """PIX Key registration for users"""
    account = models.ForeignKey(
        UserBankAccount,
        related_name='pix_keys',
        on_delete=models.CASCADE
    )
    key_type = models.CharField(max_length=10, choices=PIX_KEY_TYPE_CHOICES)
    key_value = models.CharField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['account', 'key_type']
    
    def __str__(self):
        return f"{self.get_key_type_display()}: {self.key_value}"
    
    def save(self, *args, **kwargs):
        if self.key_type == 'RANDOM' and not self.key_value:
            self.key_value = str(uuid.uuid4())
        super().save(*args, **kwargs)


class PixTransaction(models.Model):
    """PIX payment transactions"""
    from_account = models.ForeignKey(
        UserBankAccount,
        related_name='pix_sent',
        on_delete=models.CASCADE
    )
    to_key = models.ForeignKey(
        PixKey,
        related_name='pix_received',
        on_delete=models.CASCADE
    )
    amount = models.DecimalField(decimal_places=2, max_digits=12)
    description = models.CharField(max_length=255, blank=True)
    status = models.CharField(
        max_length=10,
        choices=PIX_STATUS_CHOICES,
        default=PIX_COMPLETED
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    
    transaction = models.OneToOneField(
        'transactions.Transaction',
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"PIX: {self.from_account} -> {self.to_key} (R$ {self.amount})"
