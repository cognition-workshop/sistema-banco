from django.db import models


class FeriadoBancario(models.Model):
    TIPO_CHOICES = [
        ('NACIONAL', 'Nacional'),
        ('ESTADUAL', 'Estadual'),
        ('MUNICIPAL', 'Municipal'),
    ]
    
    data = models.DateField(unique=True)
    nome = models.CharField(max_length=100)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='NACIONAL')
    ativo = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Feriado Bancário'
        verbose_name_plural = 'Feriados Bancários'
        ordering = ['data']
        indexes = [
            models.Index(fields=['data', 'ativo']),
        ]
    
    def __str__(self):
        return f"{self.nome} - {self.data}"
