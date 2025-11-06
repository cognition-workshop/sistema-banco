import hashlib
import json
from django.db import models
from django.utils import timezone
from django.conf import settings

from .constants import TRANSACTION_TYPE_CHOICES
from accounts.models import UserBankAccount


class ChavePix(models.Model):
    TIPO_CHOICES = [
        ('CPF', 'CPF'),
        ('EMAIL', 'Email'),
        ('TELEFONE', 'Telefone'),
        ('ALEATORIA', 'Chave Aleatória'),
    ]
    
    account = models.ForeignKey(
        UserBankAccount,
        related_name='chaves_pix',
        on_delete=models.CASCADE
    )
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    chave = models.CharField(max_length=255, unique=True)
    ativa = models.BooleanField(default=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = 'Chaves PIX'
        indexes = [models.Index(fields=['chave'])]
    
    def __str__(self):
        return f'{self.get_tipo_display()}: {self.chave}'


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
    
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    geolocation = models.CharField(max_length=255, null=True, blank=True)
    transaction_hash = models.CharField(max_length=64, unique=True, editable=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='transactions_created'
    )
    
    pix_destinatario_nome = models.CharField(max_length=255, null=True, blank=True)
    pix_destinatario_cpf = models.CharField(max_length=14, null=True, blank=True)
    pix_chave = models.CharField(max_length=255, null=True, blank=True)
    pix_txid = models.CharField(max_length=32, null=True, blank=True, unique=True)

    def __str__(self):
        return f'{self.account.get_account_number()} - {self.get_transaction_type_display()}'

    class Meta:
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['transaction_type']),
            models.Index(fields=['pix_txid']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.transaction_hash:
            self.transaction_hash = self._generate_hash()
        super().save(*args, **kwargs)
    
    def _generate_hash(self):
        data = {
            'account_id': self.account_id,
            'amount': str(self.amount),
            'transaction_type': self.transaction_type,
            'timestamp': str(timezone.now()),
            'balance_after': str(self.balance_after_transaction),
        }
        hash_input = json.dumps(data, sort_keys=True).encode()
        return hashlib.sha256(hash_input).hexdigest()
    
    def delete(self, *args, **kwargs):
        raise models.ProtectedError(
            "Transactions cannot be deleted due to regulatory compliance (BACEN)",
            [self]
        )


class TransferenciaPix(models.Model):
    transaction = models.OneToOneField(
        Transaction,
        on_delete=models.PROTECT,
        related_name='pix_transfer'
    )
    chave_origem = models.ForeignKey(
        ChavePix,
        on_delete=models.PROTECT,
        related_name='transferencias_enviadas'
    )
    chave_destino_valor = models.CharField(max_length=255)
    chave_destino_tipo = models.CharField(max_length=10)
    qr_code_data = models.TextField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pendente'),
            ('COMPLETED', 'Concluída'),
            ('FAILED', 'Falha'),
        ],
        default='COMPLETED'
    )
    
    class Meta:
        verbose_name = 'Transferência PIX'
        verbose_name_plural = 'Transferências PIX'
    
    def __str__(self):
        return f'PIX: {self.transaction.amount}'
    
    def generate_qr_code_data(self):
        """
        Simplified PIX QR code data generation.
        Returns a JSON string with transaction details for QR code.
        In a production system, this would follow BR Code standard (EMV).
        """
        import json
        qr_data = {
            'version': '1.0',
            'pixType': 'TRANSFER',
            'txid': self.transaction.pix_txid or '',
            'amount': str(self.transaction.amount),
            'destinatario': {
                'tipo_chave': self.chave_destino_tipo,
                'chave': self.chave_destino_valor,
            },
            'remetente': {
                'tipo_chave': self.chave_origem.tipo,
                'chave': self.chave_origem.chave,
            },
            'timestamp': self.transaction.timestamp.isoformat(),
        }
        return json.dumps(qr_data, ensure_ascii=False)
