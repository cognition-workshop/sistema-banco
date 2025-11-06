import uuid
import re
from django.db import models
from django.core.validators import EmailValidator
from django.core.exceptions import ValidationError

from accounts.models import UserBankAccount
from .constants import PIX_KEY_TYPE_CHOICES, CPF, EMAIL, PHONE, RANDOM


def validate_cpf(value):
    cpf = re.sub(r'[^0-9]', '', value)
    
    if len(cpf) != 11:
        raise ValidationError('CPF deve ter 11 dígitos')
    
    if cpf == cpf[0] * 11:
        raise ValidationError('CPF inválido')
    
    for i in range(9, 11):
        sum_value = sum(int(cpf[num]) * ((i + 1) - num) for num in range(0, i))
        digit = ((sum_value * 10) % 11) % 10
        if int(cpf[i]) != digit:
            raise ValidationError('CPF inválido')
    
    return cpf


def validate_phone(value):
    phone = re.sub(r'[^0-9]', '', value)
    
    if not phone.startswith('55'):
        raise ValidationError('Telefone deve começar com +55 (código do Brasil)')
    
    if len(phone) not in [12, 13]:
        raise ValidationError('Formato de telefone inválido')
    
    return phone


class PixKey(models.Model):
    account = models.ForeignKey(
        UserBankAccount,
        related_name='pix_keys',
        on_delete=models.CASCADE,
    )
    key_type = models.PositiveSmallIntegerField(
        choices=PIX_KEY_TYPE_CHOICES
    )
    key_value = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['account', 'key_type', 'key_value']
    
    def clean(self):
        if self.key_type == CPF:
            self.key_value = validate_cpf(self.key_value)
        elif self.key_type == EMAIL:
            validator = EmailValidator()
            validator(self.key_value)
        elif self.key_type == PHONE:
            self.key_value = validate_phone(self.key_value)
        elif self.key_type == RANDOM:
            if not self.key_value:
                self.key_value = str(uuid.uuid4())
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.get_key_type_display()}: {self.key_value}"


class PixTransaction(models.Model):
    sender_account = models.ForeignKey(
        UserBankAccount,
        related_name='pix_sent',
        on_delete=models.CASCADE,
    )
    receiver_account = models.ForeignKey(
        UserBankAccount,
        related_name='pix_received',
        on_delete=models.CASCADE,
    )
    sender_key = models.ForeignKey(
        PixKey,
        related_name='transactions_sent',
        on_delete=models.SET_NULL,
        null=True,
    )
    receiver_key = models.ForeignKey(
        PixKey,
        related_name='transactions_received',
        on_delete=models.SET_NULL,
        null=True,
    )
    amount = models.DecimalField(
        decimal_places=2,
        max_digits=12
    )
    sender_balance_after = models.DecimalField(
        decimal_places=2,
        max_digits=12
    )
    receiver_balance_after = models.DecimalField(
        decimal_places=2,
        max_digits=12
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"PIX: {self.sender_account} -> {self.receiver_account} (R$ {self.amount})"
