from django.db import models
from django.utils import timezone
from accounts.models import UserBankAccount
import uuid


class PIXKeyType(models.TextChoices):
    CPF = 'CPF', 'CPF'
    EMAIL = 'EMAIL', 'E-mail'
    PHONE = 'PHONE', 'Telefone'
    RANDOM = 'RANDOM', 'Chave Aleatória'


class PIXKey(models.Model):
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='pix_keys')
    key_type = models.CharField(max_length=10, choices=PIXKeyType.choices)
    key_value = models.CharField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'key_type', 'key_value']
    
    def __str__(self):
        return f"{self.key_type}: {self.key_value}"


class PIXTransaction(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pendente'),
        ('COMPLETED', 'Concluída'),
        ('FAILED', 'Falhou'),
    ]
    
    from_account = models.ForeignKey(UserBankAccount, on_delete=models.CASCADE, related_name='pix_sent')
    to_key = models.ForeignKey(PIXKey, on_delete=models.CASCADE, related_name='pix_received')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    end_to_end_id = models.CharField(max_length=32, unique=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    description = models.TextField(blank=True)
    
    def __str__(self):
        return f"PIX {self.end_to_end_id}: {self.amount}"


class PIXQRCode(models.Model):
    pix_key = models.ForeignKey(PIXKey, on_delete=models.CASCADE, related_name='qr_codes')
    amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    description = models.TextField(blank=True)
    qr_code_data = models.TextField()
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"QR Code for {self.pix_key}"
