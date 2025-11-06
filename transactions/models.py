from django.db import models

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
        return str(self.account.account_no)

    class Meta:
        ordering = ['timestamp']


class AuditLog(models.Model):
    user = models.ForeignKey(
        'accounts.User',
        related_name='audit_logs',
        on_delete=models.PROTECT,
        help_text='User who performed the operation'
    )
    account = models.ForeignKey(
        UserBankAccount,
        related_name='audit_logs',
        on_delete=models.PROTECT,
        help_text='Account affected by the operation'
    )
    
    operation_type = models.CharField(
        max_length=50,
        choices=[
            ('deposit', 'Deposit'),
            ('withdrawal', 'Withdrawal'),
            ('interest', 'Interest Calculation'),
        ],
        help_text='Type of balance-changing operation'
    )
    amount = models.DecimalField(
        decimal_places=2,
        max_digits=12,
        help_text='Amount involved in the operation'
    )
    
    balance_before = models.DecimalField(
        decimal_places=2,
        max_digits=12,
        help_text='Account balance before the operation'
    )
    balance_after = models.DecimalField(
        decimal_places=2,
        max_digits=12,
        help_text='Account balance after the operation'
    )
    
    timestamp = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text='When the operation occurred'
    )
    
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text='IP address of the user (for web requests)'
    )
    user_agent = models.TextField(
        null=True,
        blank=True,
        help_text='Browser user agent (for web requests)'
    )
    
    transaction = models.ForeignKey(
        Transaction,
        related_name='audit_logs',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        help_text='Related transaction record'
    )
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['account', 'timestamp']),
            models.Index(fields=['operation_type', 'timestamp']),
        ]
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
    
    def __str__(self):
        return f"{self.operation_type} - {self.account.account_no} - {self.timestamp}"
    
    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise ValueError("Audit logs cannot be modified after creation")
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        raise ValueError("Audit logs cannot be deleted")

def create_audit_log(user, account, operation_type, amount, balance_before, balance_after, 
                     transaction=None, ip_address=None, user_agent=None):
    return AuditLog.objects.create(
        user=user,
        account=account,
        operation_type=operation_type,
        amount=amount,
        balance_before=balance_before,
        balance_after=balance_after,
        transaction=transaction,
        ip_address=ip_address,
        user_agent=user_agent
    )
