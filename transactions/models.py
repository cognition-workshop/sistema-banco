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


class ChavePix(models.Model):
    TIPO_CHOICES = (
        ('CPF', 'CPF'),
        ('EMAIL', 'Email'),
        ('TELEFONE', 'Telefone'),
        ('ALEATORIA', 'Chave Aleatória'),
    )
    
    user = models.ForeignKey(
        'accounts.User',
        related_name='chaves_pix',
        on_delete=models.CASCADE
    )
    tipo_chave = models.CharField(max_length=10, choices=TIPO_CHOICES)
    chave = models.CharField(max_length=255, unique=True)
    ativa = models.BooleanField(default=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = 'Chaves PIX'
    
    def __str__(self):
        return f"{self.tipo_chave}: {self.chave}"


class TransacaoPix(models.Model):
    transaction = models.OneToOneField(
        Transaction,
        related_name='pix_data',
        on_delete=models.CASCADE
    )
    chave_origem = models.ForeignKey(
        ChavePix,
        related_name='transacoes_enviadas',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    chave_destino = models.CharField(max_length=255)
    qr_code_data = models.TextField(null=True, blank=True)
    
    def __str__(self):
        return f"PIX {self.transaction.id}"


class RelatorioIRPF(models.Model):
    user = models.ForeignKey(
        'accounts.User',
        related_name='relatorios_irpf',
        on_delete=models.CASCADE
    )
    ano_calendario = models.IntegerField()
    data_geracao = models.DateTimeField(auto_now_add=True)
    rendimentos_totais = models.DecimalField(max_digits=12, decimal_places=2)
    rendimentos_isentos = models.DecimalField(max_digits=12, decimal_places=2)
    rendimentos_tributaveis = models.DecimalField(max_digits=12, decimal_places=2)
    arquivo_pdf = models.FileField(upload_to='irpf_reports/', null=True, blank=True)
    
    class Meta:
        verbose_name = 'Relatório IRPF'
        verbose_name_plural = 'Relatórios IRPF'
        unique_together = ['user', 'ano_calendario']
        ordering = ['-ano_calendario']
    
    def __str__(self):
        return f"IRPF {self.ano_calendario} - {self.user.email}"
