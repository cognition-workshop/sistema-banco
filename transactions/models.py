import uuid
from django.db import models
from django.core.validators import EmailValidator
from django.utils import timezone
from datetime import timedelta

from .constants import (
    TRANSACTION_TYPE_CHOICES,
    PIX_KEY_TYPE_CHOICES,
    PIX_STATUS_CHOICES,
    CPF_KEY,
    EMAIL_KEY,
    PHONE_KEY,
    RANDOM_KEY,
    PIX_COMPLETED
)
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

    def __str__(self):
        return str(self.account.account_no)

    class Meta:
        ordering = ['timestamp']


class PixKey(models.Model):
    account = models.ForeignKey(
        'accounts.UserBankAccount',
        related_name='pix_keys',
        on_delete=models.CASCADE,
    )
    key_type = models.CharField(
        max_length=10,
        choices=PIX_KEY_TYPE_CHOICES
    )
    key_value = models.CharField(
        max_length=255,
        unique=True
    )
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_key_type_display()}: {self.key_value}"

    class Meta:
        unique_together = [['account', 'key_type', 'key_value']]
        ordering = ['-is_primary', '-created_at']

    def save(self, *args, **kwargs):
        if self.is_primary:
            PixKey.objects.filter(account=self.account, is_primary=True).update(is_primary=False)
        super().save(*args, **kwargs)


class PixTransaction(models.Model):
    sender_account = models.ForeignKey(
        'accounts.UserBankAccount',
        related_name='pix_sent',
        on_delete=models.CASCADE,
    )
    receiver_account = models.ForeignKey(
        'accounts.UserBankAccount',
        related_name='pix_received',
        on_delete=models.CASCADE,
    )
    pix_key_used = models.ForeignKey(
        'PixKey',
        related_name='transactions',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    amount = models.DecimalField(
        decimal_places=2,
        max_digits=12
    )
    status = models.CharField(
        max_length=10,
        choices=PIX_STATUS_CHOICES,
        default=PIX_COMPLETED
    )
    description = models.CharField(max_length=255, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"PIX: {self.sender_account.account_no} -> {self.receiver_account.account_no} (${self.amount})"

    class Meta:
        ordering = ['-timestamp']


class PixQRCode(models.Model):
    account = models.ForeignKey(
        'accounts.UserBankAccount',
        related_name='pix_qrcodes',
        on_delete=models.CASCADE,
    )
    qr_code_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False
    )
    amount = models.DecimalField(
        decimal_places=2,
        max_digits=12,
        null=True,
        blank=True,
        help_text='Deixe em branco para valor variável'
    )
    description = models.CharField(max_length=255, blank=True)
    expiration_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"QR Code: {self.qr_code_id}"

    class Meta:
        ordering = ['-created_at']

    def is_expired(self):
        return timezone.now() > self.expiration_date

    def save(self, *args, **kwargs):
        if not self.expiration_date:
            self.expiration_date = timezone.now() + timedelta(hours=24)
        super().save(*args, **kwargs)
