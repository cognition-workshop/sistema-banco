import uuid
import qrcode
from io import BytesIO
from django.db import models
from django.core.validators import RegexValidator
from accounts.models import UserBankAccount


PIX_KEY_TYPE_CHOICES = (
    ('CPF', 'CPF'),
    ('CNPJ', 'CNPJ'),
    ('EMAIL', 'Email'),
    ('PHONE', 'Phone'),
    ('RANDOM', 'Random Key'),
)

PIX_TRANSACTION_STATUS_CHOICES = (
    ('PENDING', 'Pending'),
    ('COMPLETED', 'Completed'),
    ('FAILED', 'Failed'),
    ('CANCELLED', 'Cancelled'),
)


class PixKey(models.Model):
    account = models.ForeignKey(
        UserBankAccount,
        related_name='pix_keys',
        on_delete=models.CASCADE,
    )
    key_type = models.CharField(
        max_length=10,
        choices=PIX_KEY_TYPE_CHOICES
    )
    key_value = models.CharField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['account', 'key_type', 'key_value']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.key_type}: {self.key_value}"

    def validate_key(self):
        if self.key_type == 'CPF':
            cpf_validator = RegexValidator(
                regex=r'^\d{3}\.\d{3}\.\d{3}-\d{2}$',
                message='CPF must be in format XXX.XXX.XXX-XX'
            )
            cpf_validator(self.key_value)
        elif self.key_type == 'CNPJ':
            cnpj_validator = RegexValidator(
                regex=r'^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$',
                message='CNPJ must be in format XX.XXX.XXX/XXXX-XX'
            )
            cnpj_validator(self.key_value)
        elif self.key_type == 'EMAIL':
            from django.core.validators import EmailValidator
            email_validator = EmailValidator()
            email_validator(self.key_value)
        elif self.key_type == 'PHONE':
            phone_validator = RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message='Phone number must be entered in the format: +999999999. Up to 15 digits allowed.'
            )
            phone_validator(self.key_value)

    def save(self, *args, **kwargs):
        if self.key_type == 'RANDOM' and not self.key_value:
            self.key_value = str(uuid.uuid4())
        self.validate_key()
        super().save(*args, **kwargs)


class PixTransaction(models.Model):
    transaction_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    sender_account = models.ForeignKey(
        UserBankAccount,
        related_name='pix_sent',
        on_delete=models.CASCADE,
    )
    receiver_key = models.ForeignKey(
        PixKey,
        related_name='pix_received',
        on_delete=models.PROTECT,
    )
    amount = models.DecimalField(
        decimal_places=2,
        max_digits=12
    )
    description = models.CharField(max_length=255, blank=True)
    status = models.CharField(
        max_length=10,
        choices=PIX_TRANSACTION_STATUS_CHOICES,
        default='PENDING'
    )
    qr_code = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    geolocation = models.CharField(max_length=255, null=True, blank=True)
    channel = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"PIX {self.transaction_id}: {self.sender_account} -> {self.receiver_key}"

    def generate_qr_code(self):
        pix_data = f"PIX|{self.transaction_id}|{self.amount}|{self.receiver_key.key_value}"
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(pix_data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        
        import base64
        self.qr_code = base64.b64encode(buffer.getvalue()).decode()
        return self.qr_code

    def process_transaction(self):
        from django.utils import timezone
        from transactions.models import Transaction, FailedTransaction
        from transactions.constants import DEPOSIT, WITHDRAWAL
        
        try:
            if self.sender_account.balance < self.amount:
                raise ValueError("Insufficient funds")
            
            sender_balance = self.sender_account.balance - self.amount
            receiver_balance = self.receiver_key.account.balance + self.amount
            
            sender_transaction = Transaction.objects.create(
                account=self.sender_account,
                amount=-self.amount,
                balance_after_transaction=sender_balance,
                transaction_type=WITHDRAWAL,
                ip_address=self.ip_address,
                geolocation=self.geolocation,
                channel=self.channel,
            )
            
            receiver_transaction = Transaction.objects.create(
                account=self.receiver_key.account,
                amount=self.amount,
                balance_after_transaction=receiver_balance,
                transaction_type=DEPOSIT,
                ip_address=self.ip_address,
                geolocation=self.geolocation,
                channel=self.channel,
            )
            
            self.sender_account.balance = sender_balance
            self.receiver_key.account.balance = receiver_balance
            self.sender_account.save()
            self.receiver_key.account.save()
            
            self.status = 'COMPLETED'
            self.completed_at = timezone.now()
            self.save()
            
            return True
            
        except Exception as e:
            self.status = 'FAILED'
            self.error_message = str(e)
            self.save()
            
            FailedTransaction.objects.create(
                account=self.sender_account,
                amount=self.amount,
                transaction_type=WITHDRAWAL,
                ip_address=self.ip_address,
                geolocation=self.geolocation,
                channel=self.channel,
                error_message=str(e),
                error_code='PIX_FAILED',
            )
            
            return False
