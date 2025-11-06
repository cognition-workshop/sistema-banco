from django.db import models
from django.core.validators import RegexValidator
from accounts.models import UserBankAccount
import secrets
import string

class ChavePix(models.Model):
    TIPO_CHOICES = [
        ('CPF', 'CPF'),
        ('EMAIL', 'Email'),
        ('TELEFONE', 'Telefone'),
        ('ALEATORIA', 'Chave Aleatória'),
    ]
    
    account = models.ForeignKey(
        UserBankAccount,
        on_delete=models.CASCADE,
        related_name='chaves_pix'
    )
    tipo = models.CharField('Tipo de Chave', max_length=10, choices=TIPO_CHOICES)
    chave = models.CharField('Chave PIX', max_length=255, unique=True)
    ativa = models.BooleanField('Ativa', default=True)
    criada_em = models.DateTimeField('Criada em', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Chave PIX'
        verbose_name_plural = 'Chaves PIX'
        unique_together = ['account', 'tipo']
    
    def __str__(self):
        return f"{self.tipo}: {self.chave}"
    
    @staticmethod
    def gerar_chave_aleatoria():
        """Gera uma chave PIX aleatória no formato padrão brasileiro"""
        characters = string.ascii_lowercase + string.digits
        return ''.join(secrets.choice(characters) for _ in range(32))


class TransacaoPix(models.Model):
    STATUS_CHOICES = [
        ('PENDENTE', 'Pendente'),
        ('CONCLUIDA', 'Concluída'),
        ('ERRO', 'Erro'),
    ]
    
    conta_origem = models.ForeignKey(
        UserBankAccount,
        on_delete=models.CASCADE,
        related_name='pix_enviados'
    )
    chave_destino = models.CharField('Chave PIX Destino', max_length=255)
    conta_destino = models.ForeignKey(
        UserBankAccount,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pix_recebidos'
    )
    valor = models.DecimalField('Valor', max_digits=12, decimal_places=2)
    descricao = models.CharField('Descrição', max_length=255, blank=True)
    status = models.CharField('Status', max_length=10, choices=STATUS_CHOICES, default='PENDENTE')
    timestamp = models.DateTimeField('Data/Hora', auto_now_add=True)
    erro_mensagem = models.TextField('Mensagem de Erro', blank=True)
    
    class Meta:
        verbose_name = 'Transação PIX'
        verbose_name_plural = 'Transações PIX'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"PIX R$ {self.valor} - {self.status}"
