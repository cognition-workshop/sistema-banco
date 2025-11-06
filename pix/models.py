from django.db import models
from django.core.validators import EmailValidator, RegexValidator
from accounts.models import UserBankAccount
from transactions.models import Transaction
import uuid


class PixKeyType(models.TextChoices):
    CPF = 'CPF', 'CPF'
    EMAIL = 'EMAIL', 'Email'
    PHONE = 'PHONE', 'Telefone'
    RANDOM = 'RANDOM', 'Chave Aleatória'


class PixKey(models.Model):
    account = models.ForeignKey(
        UserBankAccount,
        related_name='pix_keys',
        on_delete=models.CASCADE
    )
    key_type = models.CharField(
        max_length=10,
        choices=PixKeyType.choices
    )
    key_value = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = [['account', 'key_type']]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.key_type}: {self.key_value}"

    @staticmethod
    def generate_random_key():
        """Generate a random PIX key (UUID format)"""
        return str(uuid.uuid4())


class PixTransaction(models.Model):
    transaction = models.OneToOneField(
        Transaction,
        related_name='pix_transaction',
        on_delete=models.CASCADE
    )
    pix_key_used = models.ForeignKey(
        PixKey,
        related_name='transactions',
        on_delete=models.SET_NULL,
        null=True
    )
    sender_account = models.ForeignKey(
        UserBankAccount,
        related_name='pix_sent',
        on_delete=models.CASCADE
    )
    receiver_account = models.ForeignKey(
        UserBankAccount,
        related_name='pix_received',
        on_delete=models.CASCADE
    )
    description = models.CharField(max_length=255, blank=True)
    end_to_end_id = models.CharField(max_length=32, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.end_to_end_id:
            from django.utils import timezone
            timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
            self.end_to_end_id = f"E{timestamp}{str(uuid.uuid4())[:8]}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"PIX {self.sender_account} -> {self.receiver_account}: {self.transaction.amount}"


class PixQRCode(models.Model):
    account = models.ForeignKey(
        UserBankAccount,
        related_name='pix_qrcodes',
        on_delete=models.CASCADE
    )
    pix_key = models.ForeignKey(
        PixKey,
        related_name='qrcodes',
        on_delete=models.CASCADE
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Leave empty for dynamic amount'
    )
    description = models.CharField(max_length=255, blank=True)
    qr_code_image = models.ImageField(upload_to='pix_qrcodes/', blank=True)
    qr_code_payload = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"QR Code for {self.pix_key.key_value}"
