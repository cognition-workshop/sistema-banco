from django.contrib import admin
from .models import ChavePix, TransacaoPix

@admin.register(ChavePix)
class ChavePixAdmin(admin.ModelAdmin):
    list_display = ['chave', 'tipo', 'account', 'ativa', 'criada_em']
    list_filter = ['tipo', 'ativa']
    search_fields = ['chave', 'account__user__email']

@admin.register(TransacaoPix)
class TransacaoPixAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'conta_origem', 'chave_destino', 'valor', 'status']
    list_filter = ['status', 'timestamp']
    search_fields = ['chave_destino', 'conta_origem__user__email']
    readonly_fields = ['timestamp']
