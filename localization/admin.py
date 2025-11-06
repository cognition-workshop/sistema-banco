from django.contrib import admin
from .models import ChavePIX, TransacaoPIX, Feriado, AuditLog


@admin.register(ChavePIX)
class ChavePIXAdmin(admin.ModelAdmin):
    list_display = ['chave', 'tipo', 'usuario', 'ativa', 'data_cadastro']
    list_filter = ['tipo', 'ativa']
    search_fields = ['chave', 'usuario__email']
    readonly_fields = ['data_cadastro', 'data_inativacao']


@admin.register(TransacaoPIX)
class TransacaoPIXAdmin(admin.ModelAdmin):
    list_display = ['identificador_transacao', 'conta_origem', 'valor', 'status', 'data_transacao']
    list_filter = ['status', 'data_transacao']
    search_fields = ['identificador_transacao', 'chave_pix_destino']
    readonly_fields = ['data_transacao', 'identificador_transacao']


@admin.register(Feriado)
class FeriadoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'data', 'tipo', 'recorrente']
    list_filter = ['tipo', 'recorrente']
    search_fields = ['nome']
    ordering = ['data']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'tipo_operacao', 'valor', 'timestamp']
    list_filter = ['tipo_operacao', 'timestamp']
    search_fields = ['usuario__email', 'descricao']
    readonly_fields = ['usuario', 'conta', 'tipo_operacao', 'valor', 'saldo_anterior', 
                       'saldo_posterior', 'descricao', 'timestamp', 'hash_registro', 
                       'hash_anterior', 'ip_address']
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
