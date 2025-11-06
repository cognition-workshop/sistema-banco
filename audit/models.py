from django.db import models
from django.contrib.auth import get_user_model
import hashlib
import json
from django.utils import timezone

User = get_user_model()


class AuditLog(models.Model):
    timestamp = models.DateTimeField('Data/Hora', auto_now_add=True, editable=False)
    usuario = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        verbose_name='Usuário',
        editable=False
    )
    tipo_transacao = models.CharField(
        'Tipo de Transação',
        max_length=50,
        editable=False
    )
    dados_transacao = models.JSONField(
        'Dados da Transação',
        editable=False
    )
    hash_anterior = models.CharField(
        'Hash da Transação Anterior',
        max_length=64,
        blank=True,
        editable=False
    )
    hash_atual = models.CharField(
        'Hash da Transação Atual',
        max_length=64,
        editable=False,
        unique=True
    )
    
    class Meta:
        verbose_name = 'Log de Auditoria'
        verbose_name_plural = 'Logs de Auditoria'
        ordering = ['timestamp']
        
    def __str__(self):
        return f"{self.timestamp} - {self.tipo_transacao}"
    
    def save(self, *args, **kwargs):
        if not self.hash_atual:
            ultimo_log = AuditLog.objects.order_by('-timestamp').first()
            self.hash_anterior = ultimo_log.hash_atual if ultimo_log else ''
            
            self.hash_atual = self.calcular_hash()
        
        super().save(*args, **kwargs)
    
    def calcular_hash(self):
        """Calculate SHA256 hash for immutability chain"""
        dados = {
            'timestamp': self.timestamp.isoformat() if self.timestamp else timezone.now().isoformat(),
            'usuario_id': self.usuario_id,
            'tipo_transacao': self.tipo_transacao,
            'dados_transacao': self.dados_transacao,
            'hash_anterior': self.hash_anterior,
        }
        dados_str = json.dumps(dados, sort_keys=True)
        return hashlib.sha256(dados_str.encode()).hexdigest()
    
    def delete(self, *args, **kwargs):
        """Prevent deletion to maintain immutability"""
        raise Exception('Logs de auditoria não podem ser deletados (requerimento BACEN)')
    
    def verificar_integridade(self):
        """Verify hash integrity"""
        hash_calculado = self.calcular_hash()
        return hash_calculado == self.hash_atual
