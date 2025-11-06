from django.db import models
from django.core.exceptions import ValidationError

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
    ip_address = models.CharField(max_length=45, blank=True, null=True)
    geolocation = models.CharField(max_length=255, blank=True, null=True)
    channel = models.CharField(max_length=20, blank=True, null=True)
    hash_signature = models.CharField(max_length=64, blank=True, null=True)

    def __str__(self):
        return str(self.account.account_no)

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValidationError("Transações não podem ser modificadas após criação")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Transações não podem ser deletadas")

    class Meta:
        ordering = ['timestamp']


class FailedTransaction(models.Model):
    account = models.ForeignKey(
        UserBankAccount,
        related_name='failed_transactions',
        on_delete=models.CASCADE,
    )
    attempted_amount = models.DecimalField(
        decimal_places=2,
        max_digits=12
    )
    attempted_transaction_type = models.PositiveSmallIntegerField(
        choices=TRANSACTION_TYPE_CHOICES
    )
    failure_reason = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.CharField(max_length=45, blank=True, null=True)
    geolocation = models.CharField(max_length=255, blank=True, null=True)
    channel = models.CharField(max_length=20, blank=True, null=True)
    hash_signature = models.CharField(max_length=64, blank=True, null=True)

    def __str__(self):
        return f"Failed {self.get_attempted_transaction_type_display()} - {self.account.account_no}"

    class Meta:
        ordering = ['-timestamp']
