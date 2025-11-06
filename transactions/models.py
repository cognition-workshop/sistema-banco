from django.db import models
from django.conf import settings
import hashlib

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

    def __str__(self):
        return str(self.account.account_no) if self.account.account_no else str(self.account)

    class Meta:
        ordering = ['timestamp']
    
    def save(self, *args, **kwargs):
        if self.pk:
            raise ValueError('Transactions cannot be modified after creation (BACEN compliance)')
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        raise ValueError('Transactions cannot be deleted (BACEN compliance)')


class AuditLog(models.Model):
    """
    Immutable audit log for BACEN compliance with blockchain-style hashing
    """
    transaction = models.ForeignKey(
        'Transaction',
        related_name='audit_logs',
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    action = models.CharField(max_length=50, help_text='Action performed')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    previous_hash = models.CharField(max_length=64, blank=True)
    current_hash = models.CharField(max_length=64, unique=True, db_index=True)
    data_snapshot = models.JSONField(help_text='Snapshot of transaction data')
    
    class Meta:
        ordering = ['timestamp']
        
    def save(self, *args, **kwargs):
        if self.pk:
            raise ValueError('AuditLog entries cannot be modified')
        
        last_log = AuditLog.objects.order_by('-timestamp').first()
        self.previous_hash = last_log.current_hash if last_log else '0' * 64
        
        hash_data = f'{self.previous_hash}{self.action}{self.timestamp}{self.data_snapshot}'
        self.current_hash = hashlib.sha256(hash_data.encode()).hexdigest()
        
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        raise ValueError('AuditLog entries cannot be deleted')


class PixKey(models.Model):
    """PIX key registration for accounts"""
    account = models.ForeignKey(
        'accounts.UserBankAccount',
        related_name='pix_keys',
        on_delete=models.CASCADE
    )
    key_type = models.CharField(max_length=10)
    key_value = models.CharField(max_length=255, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['account', 'key_type']
        
    def __str__(self):
        return f'{self.key_type}: {self.key_value}'


class PixTransaction(models.Model):
    """PIX transfer transaction record"""
    transaction = models.OneToOneField(
        Transaction,
        related_name='pix_detail',
        on_delete=models.PROTECT
    )
    sender_account = models.ForeignKey(
        'accounts.UserBankAccount',
        related_name='pix_sent',
        on_delete=models.PROTECT
    )
    receiver_account = models.ForeignKey(
        'accounts.UserBankAccount',
        related_name='pix_received',
        on_delete=models.PROTECT
    )
    pix_key_used = models.ForeignKey(
        PixKey,
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    description = models.CharField(max_length=255, blank=True)
    
    def __str__(self):
        return f'PIX: {self.sender_account} -> {self.receiver_account}'


class PixQRCode(models.Model):
    """PIX QR Code for payments"""
    QR_TYPE_STATIC = 'STATIC'
    QR_TYPE_DYNAMIC = 'DYNAMIC'
    QR_TYPE_CHOICES = (
        (QR_TYPE_STATIC, 'Static'),
        (QR_TYPE_DYNAMIC, 'Dynamic'),
    )
    
    account = models.ForeignKey(
        'accounts.UserBankAccount',
        related_name='pix_qr_codes',
        on_delete=models.CASCADE
    )
    qr_type = models.CharField(max_length=10, choices=QR_TYPE_CHOICES)
    qr_code_data = models.TextField(help_text='QR code payload')
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Fixed amount for dynamic QR codes'
    )
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f'{self.qr_type} QR Code for {self.account}'
