from django.contrib import admin
from .models import RelatorioIRPF


@admin.register(RelatorioIRPF)
class RelatorioIRPFAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'ano_calendario', 'rendimentos_juros', 'gerado_em']
    list_filter = ['ano_calendario', 'gerado_em']
    search_fields = ['usuario__email']
    readonly_fields = ['gerado_em']
