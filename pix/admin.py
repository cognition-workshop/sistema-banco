from django.contrib import admin
from .models import ChavePix, TransacaoPix


@admin.register(ChavePix)
class ChavePixAdmin(admin.ModelAdmin):
    list_display = ['tipo', 'valor', 'conta', 'ativa', 'criada_em']
    list_filter = ['tipo', 'ativa', 'criada_em']
    search_fields = ['valor', 'conta__user__email']


@admin.register(TransacaoPix)
class TransacaoPixAdmin(admin.ModelAdmin):
    list_display = ['conta_origem', 'conta_destino', 'valor', 'status', 'timestamp']
    list_filter = ['status', 'timestamp']
    search_fields = ['conta_origem__user__email', 'conta_destino__user__email']
