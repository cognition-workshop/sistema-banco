import uuid
import hashlib
import json
from django.db import models
from django.contrib.auth import get_user_model
from accounts.models import UserBankAccount

User = get_user_model()

EVENTOS_BACEN = [
    ('USER_CREATED', 'Usuário Criado'),
    ('USER_UPDATED', 'Usuário Atualizado'),
    ('ACCOUNT_CREATED', 'Conta Criada'),
    ('ACCOUNT_UPDATED', 'Conta Atualizada'),
    ('TRANSACTION_CREATED', 'Transação Criada'),
    ('PIX_TRANSFER', 'Transferência PIX'),
    ('LOGIN', 'Login'),
    ('LOGOUT', 'Logout'),
]


class ImmutableManager(models.Manager):
    """Manager that prevents deletion and updates"""
    
    def update(self, *args, **kwargs):
        raise NotImplementedError('BacenAuditLog records cannot be updated')
    
    def delete(self, *args, **kwargs):
        raise NotImplementedError('BacenAuditLog records cannot be deleted')


class BacenAuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    evento_tipo = models.CharField(max_length=50, choices=EVENTOS_BACEN, db_index=True)
    usuario = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    conta_afetada = models.ForeignKey(UserBankAccount, null=True, blank=True, on_delete=models.SET_NULL)
    dados_anteriores = models.JSONField(default=dict, blank=True)
    dados_posteriores = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    hash_integridade = models.CharField(max_length=64, editable=False)
    hash_anterior = models.CharField(max_length=64, null=True, blank=True, editable=False)
    
    objects = ImmutableManager()
    
    class Meta:
        verbose_name = 'Log de Auditoria BACEN'
        verbose_name_plural = 'Logs de Auditoria BACEN'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp', 'evento_tipo']),
            models.Index(fields=['usuario', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.evento_tipo} - {self.timestamp}"
    
    def save(self, *args, **kwargs):
        if not self.hash_integridade:
            self.hash_integridade = self.calcular_hash()
        super().save(*args, **kwargs)
    
    def calcular_hash(self):
        """Calculate SHA256 hash for integrity"""
        data = {
            'evento_tipo': self.evento_tipo,
            'timestamp': str(self.timestamp),
            'dados_anteriores': self.dados_anteriores,
            'dados_posteriores': self.dados_posteriores,
            'hash_anterior': self.hash_anterior or '',
        }
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    def delete(self, *args, **kwargs):
        raise NotImplementedError('BacenAuditLog records cannot be deleted')
