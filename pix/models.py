from django.db import models
from django.core.exceptions import ValidationError
from accounts.models import UserBankAccount
import re


class TipoChavePix(models.TextChoices):
    CPF = 'CPF', 'CPF'
    EMAIL = 'EMAIL', 'Email'
    CELULAR = 'CELULAR', 'Celular'
    ALEATORIA = 'ALEATORIA', 'Chave Aleatória'


class ChavePix(models.Model):
    conta = models.ForeignKey(
        UserBankAccount,
        on_delete=models.CASCADE,
        related_name='chaves_pix'
    )
    tipo = models.CharField(
        max_length=20,
        choices=TipoChavePix.choices
    )
    valor = models.CharField(
        max_length=200,
        unique=True,
        help_text='Valor da chave PIX'
    )
    ativa = models.BooleanField(default=True)
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Chave PIX'
        verbose_name_plural = 'Chaves PIX'
        indexes = [
            models.Index(fields=['conta', 'ativa']),
        ]

    def __str__(self):
        return f"{self.tipo}: {self.valor}"

    def clean(self):
        if self.tipo == TipoChavePix.CPF:
            from accounts.validators import validate_cpf
            validate_cpf(self.valor)
        
        elif self.tipo == TipoChavePix.EMAIL:
            from django.core.validators import EmailValidator
            validator = EmailValidator()
            validator(self.valor)
        
        elif self.tipo == TipoChavePix.CELULAR:
            pattern = r'^\(\d{2}\) \d{5}-\d{4}$'
            if not re.match(pattern, self.valor):
                raise ValidationError('Celular deve estar no formato (XX) XXXXX-XXXX')
        
        if not self.pk:
            existing_keys = ChavePix.objects.filter(conta=self.conta, ativa=True).count()
            if existing_keys >= 5:
                raise ValidationError('Limite de 5 chaves PIX por conta atingido')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class TransacaoPix(models.Model):
    STATUS_CHOICES = [
        ('PROCESSANDO', 'Processando'),
        ('CONCLUIDO', 'Concluído'),
        ('FALHOU', 'Falhou'),
    ]
    
    conta_origem = models.ForeignKey(
        UserBankAccount,
        on_delete=models.CASCADE,
        related_name='pix_enviados'
    )
    chave_destino = models.ForeignKey(
        ChavePix,
        on_delete=models.CASCADE,
        related_name='transacoes_recebidas'
    )
    conta_destino = models.ForeignKey(
        UserBankAccount,
        on_delete=models.CASCADE,
        related_name='pix_recebidos'
    )
    valor = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )
    descricao = models.CharField(
        max_length=140,
        blank=True,
        help_text='Descrição da transferência (máximo 140 caracteres)'
    )
    qr_code_payload = models.TextField(
        blank=True,
        help_text='Payload do QR Code EMVCo'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PROCESSANDO'
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Transação PIX'
        verbose_name_plural = 'Transações PIX'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['conta_origem', '-timestamp']),
            models.Index(fields=['conta_destino', '-timestamp']),
        ]

    def __str__(self):
        return f"PIX {self.valor} de {self.conta_origem} para {self.conta_destino}"
