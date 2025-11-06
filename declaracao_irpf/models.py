from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class RelatorioIRPF(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='relatorios_irpf')
    ano_calendario = models.IntegerField(db_index=True)
    rendimentos_juros = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_depositado = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_sacado = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    saldo_31_dezembro = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gerado_em = models.DateTimeField(auto_now_add=True)
    arquivo_pdf = models.FileField(upload_to='irpf/', blank=True)
    
    class Meta:
        verbose_name = 'Relatório IRPF'
        verbose_name_plural = 'Relatórios IRPF'
        unique_together = ['usuario', 'ano_calendario']
        ordering = ['-ano_calendario', '-gerado_em']
    
    def __str__(self):
        return f"IRPF {self.ano_calendario} - {self.usuario.email}"
