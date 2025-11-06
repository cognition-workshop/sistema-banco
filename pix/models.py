from django.db import models
from django.core.validators import EmailValidator
from accounts.models import UserBankAccount
from transactions.models import Transaction
import uuid


PIX_KEY_TYPE_CHOICES = (
    ('CPF', 'CPF'),
    ('EMAIL', 'Email'),
    ('PHONE', 'Telefone'),
    ('RANDOM', 'Chave Aleatória'),
)


class PixKey(models.Model):
    """PIX key registration."""
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
        unique_together = ('account', 'key_type')
    
    def __str__(self):
        return f"{self.key_type}: {self.key_value}"
    
    def save(self, *args, **kwargs):
        if self.key_type == 'RANDOM' and not self.key_value:
            self.key_value = str(uuid.uuid4())
        super().save(*args, **kwargs)


class PixTransaction(models.Model):
    """PIX transaction record."""
    transaction = models.OneToOneField(
        Transaction,
        on_delete=models.CASCADE,
        related_name='pix_transaction'
    )
    pix_key_used = models.ForeignKey(
        PixKey,
        on_delete=models.PROTECT,
        related_name='transactions'
    )
    recipient_account = models.ForeignKey(
        UserBankAccount,
        on_delete=models.CASCADE,
        related_name='pix_received'
    )
    sender_account = models.ForeignKey(
        UserBankAccount,
        on_delete=models.CASCADE,
        related_name='pix_sent'
    )
    description = models.CharField(max_length=255, blank=True)
    
    def __str__(self):
        return f"PIX: {self.sender_account} -> {self.recipient_account}"


class PixQRCode(models.Model):
    """PIX QR Code for payment requests."""
    account = models.ForeignKey(
        UserBankAccount,
        related_name='pix_qrcodes',
        on_delete=models.CASCADE
    )
    pix_key = models.ForeignKey(
        PixKey,
        on_delete=models.CASCADE
    )
    amount = models.DecimalField(
        decimal_places=2,
        max_digits=12,
        null=True,
        blank=True,
        help_text='Leave blank for dynamic amount'
    )
    description = models.CharField(max_length=255, blank=True)
    qr_code_image = models.ImageField(upload_to='pix_qrcodes/', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    def generate_qr_code(self):
        """Generate QR code image."""
        import qrcode
        from io import BytesIO
        from django.core.files import File
        
        payload = f"PIX:{self.pix_key.key_value}:{self.amount or 0}:{self.description}"
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(payload)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        filename = f'pix_qr_{self.id}.png'
        self.qr_code_image.save(filename, File(buffer), save=False)
    
    def __str__(self):
        return f"QR Code: {self.pix_key.key_value}"
