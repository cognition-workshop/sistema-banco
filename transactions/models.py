from django.db import models

from .constants import TRANSACTION_TYPE_CHOICES, PIX_KEY_TYPES
from accounts.models import UserBankAccount, User


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


class PIXKey(models.Model):
    user = models.ForeignKey(
        User,
        related_name='pix_keys',
        on_delete=models.CASCADE
    )
    key_type = models.CharField(
        max_length=10,
        choices=PIX_KEY_TYPES
    )
    key_value = models.CharField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'key_type', 'key_value')

    def __str__(self):
        return f'{self.get_key_type_display()}: {self.key_value}'


class PIXTransaction(models.Model):
    transaction = models.OneToOneField(
        Transaction,
        related_name='pix_details',
        on_delete=models.CASCADE
    )
    e2e_id = models.CharField(
        max_length=255,
        unique=True,
        help_text='End-to-End ID for PIX transaction'
    )
    payer_info = models.JSONField()
    payee_info = models.JSONField()
    pix_key_used = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'PIX {self.e2e_id}'
