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


class BankingHoliday(models.Model):
    date = models.DateField(
        unique=True,
        help_text='Date of the banking holiday'
    )
    name = models.CharField(
        max_length=255,
        help_text='Name of the holiday'
    )
    is_national = models.BooleanField(
        default=True,
        help_text='Whether this is a national holiday'
    )

    class Meta:
        ordering = ['date']
        indexes = [
            models.Index(fields=['date']),
        ]

    def __str__(self):
        return f"{self.name} - {self.date}"

    @classmethod
    def is_business_day(cls, date):
        if date.weekday() in (5, 6):
            return False
        
        return not cls.objects.filter(date=date).exists()
