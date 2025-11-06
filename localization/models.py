from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from accounts.models import User, UserBankAccount


class ChavePIX(models.Model):
    """Chaves PIX cadastradas por usuários"""
    TIPO_CHOICES = (
        ('CPF', 'CPF'),
        ('EMAIL', 'Email'),
        ('TELEFONE', 'Telefone'),
        ('ALEATORIA', 'Chave Aleatória'),
    )
    
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='chaves_pix'
    )
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    chave = models.CharField(max_length=255, unique=True)
    ativa = models.BooleanField(default=True)
    data_cadastro = models.DateTimeField(auto_now_add=True)
    data_inativacao = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Chave PIX'
        verbose_name_plural = 'Chaves PIX'
        ordering = ['-data_cadastro']
    
    def __str__(self):
        return f'{self.tipo}: {self.chave}'


class TransacaoPIX(models.Model):
    """Transações PIX realizadas"""
    STATUS_CHOICES = (
        ('PENDENTE', 'Pendente'),
        ('CONCLUIDA', 'Concluída'),
        ('FALHA', 'Falha'),
        ('CANCELADA', 'Cancelada'),
    )
    
    conta_origem = models.ForeignKey(
        UserBankAccount,
        on_delete=models.PROTECT,
        related_name='transacoes_pix_enviadas'
    )
    conta_destino = models.ForeignKey(
        UserBankAccount,
        on_delete=models.PROTECT,
        related_name='transacoes_pix_recebidas',
        null=True,
        blank=True
    )
    chave_pix_destino = models.CharField(max_length=255)
    valor = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    descricao = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDENTE')
    data_transacao = models.DateTimeField(auto_now_add=True)
    identificador_transacao = models.CharField(max_length=100, unique=True)
    qr_code = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = 'Transação PIX'
        verbose_name_plural = 'Transações PIX'
        ordering = ['-data_transacao']
    
    def __str__(self):
        return f'PIX {self.identificador_transacao} - R$ {self.valor}'


class Feriado(models.Model):
    """Feriados bancários brasileiros"""
    TIPO_CHOICES = (
        ('NACIONAL', 'Nacional'),
        ('ESTADUAL', 'Estadual'),
        ('MUNICIPAL', 'Municipal'),
    )
    
    nome = models.CharField(max_length=255)
    data = models.DateField(unique=True)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    recorrente = models.BooleanField(
        default=False,
        help_text='Se True, o feriado ocorre anualmente na mesma data'
    )
    
    class Meta:
        verbose_name = 'Feriado'
        verbose_name_plural = 'Feriados'
        ordering = ['data']
    
    def __str__(self):
        return f'{self.nome} - {self.data}'


class AuditLog(models.Model):
    """Log de auditoria imutável para conformidade BACEN"""
    TIPO_OPERACAO_CHOICES = (
        ('DEPOSITO', 'Depósito'),
        ('SAQUE', 'Saque'),
        ('TRANSFERENCIA', 'Transferência'),
        ('PIX', 'PIX'),
        ('JUROS', 'Juros'),
    )
    
    usuario = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='audit_logs'
    )
    conta = models.ForeignKey(
        UserBankAccount,
        on_delete=models.PROTECT,
        related_name='audit_logs'
    )
    tipo_operacao = models.CharField(max_length=20, choices=TIPO_OPERACAO_CHOICES)
    valor = models.DecimalField(max_digits=12, decimal_places=2)
    saldo_anterior = models.DecimalField(max_digits=12, decimal_places=2)
    saldo_posterior = models.DecimalField(max_digits=12, decimal_places=2)
    descricao = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    hash_registro = models.CharField(max_length=64, unique=True)
    hash_anterior = models.CharField(max_length=64, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Log de Auditoria'
        verbose_name_plural = 'Logs de Auditoria'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['usuario', '-timestamp']),
            models.Index(fields=['conta', '-timestamp']),
        ]
    
    def __str__(self):
        return f'{self.tipo_operacao} - {self.usuario.email} - {self.timestamp}'
