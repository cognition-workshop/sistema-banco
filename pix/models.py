import uuid
from django.db import models
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from accounts.models import UserBankAccount


class PixKeyType(models.TextChoices):
    CPF = 'CPF', 'CPF'
    EMAIL = 'EMAIL', 'Email'
    PHONE = 'PHONE', 'Phone'
    RANDOM = 'RANDOM', 'Random Key'


class PixKey(models.Model):
    account = models.ForeignKey(
        UserBankAccount,
        related_name='pix_keys',
        on_delete=models.CASCADE,
    )
    key_type = models.CharField(
        max_length=10,
        choices=PixKeyType.choices,
    )
    key_value = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = [['key_value', 'key_type']]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.key_type}: {self.key_value}"

    def clean(self):
        if self.key_type == PixKeyType.CPF:
            self._validate_cpf()
        elif self.key_type == PixKeyType.EMAIL:
            self._validate_email()
        elif self.key_type == PixKeyType.PHONE:
            self._validate_phone()
        elif self.key_type == PixKeyType.RANDOM:
            if not self.key_value:
                self.key_value = str(uuid.uuid4())

    def _validate_cpf(self):
        cpf = ''.join(filter(str.isdigit, self.key_value))
        if len(cpf) != 11:
            raise ValidationError('CPF must have 11 digits')
        self.key_value = cpf

    def _validate_email(self):
        from django.core.validators import validate_email
        try:
            validate_email(self.key_value)
        except ValidationError:
            raise ValidationError('Invalid email format')

    def _validate_phone(self):
        phone = ''.join(filter(str.isdigit, self.key_value))
        if not (10 <= len(phone) <= 13):
            raise ValidationError('Phone must have between 10 and 13 digits')
        self.key_value = phone

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
