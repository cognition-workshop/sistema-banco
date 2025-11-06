import hashlib
import json
from django.db import models
from django.contrib.contenttypes.models import ContentType


class FeriadoBancario(models.Model):
    TIPO_CHOICES = (
        ('NACIONAL', 'Nacional'),
        ('ESTADUAL', 'Estadual'),
        ('MUNICIPAL', 'Municipal'),
    )
    
    data = models.DateField(unique=True)
    descricao = models.CharField(max_length=255)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, default='NACIONAL')
    recorrente = models.BooleanField(
        default=False,
        help_text='Se True, o feriado se repete anualmente'
    )
    
    class Meta:
        verbose_name = 'Feriado Bancário'
        verbose_name_plural = 'Feriados Bancários'
        ordering = ['data']
    
    def __str__(self):
        return f"{self.data} - {self.descricao}"


class AuditLog(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    acao = models.CharField(max_length=50)
    modelo = models.CharField(max_length=100)
    objeto_id = models.IntegerField()
    dados_anteriores = models.JSONField(null=True, blank=True)
    dados_novos = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    hash_integridade = models.CharField(max_length=64, editable=False)
    
    class Meta:
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        ordering = ['-timestamp']
    
    def save(self, *args, **kwargs):
        if not self.hash_integridade:
            data = f"{self.timestamp}{self.user_id}{self.acao}{self.modelo}{self.objeto_id}"
            self.hash_integridade = hashlib.sha256(data.encode()).hexdigest()
        
        if self.pk:
            raise ValueError("AuditLog records cannot be modified")
        
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        raise ValueError("AuditLog records cannot be deleted")
    
    def __str__(self):
        return f"{self.timestamp} - {self.acao} - {self.modelo}"
