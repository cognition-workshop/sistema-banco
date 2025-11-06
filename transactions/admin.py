from django.contrib import admin

from transactions.models import Transaction, ChavePix, TransferenciaPix


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['id', 'account', 'transaction_type', 'amount', 'timestamp', 'transaction_hash']
    list_filter = ['transaction_type', 'timestamp']
    search_fields = ['transaction_hash', 'account__cpf']
    readonly_fields = ['transaction_hash', 'timestamp']
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ChavePix)
class ChavePixAdmin(admin.ModelAdmin):
    list_display = ['chave', 'tipo', 'account', 'ativa']
    list_filter = ['tipo', 'ativa']
    search_fields = ['chave']


@admin.register(TransferenciaPix)
class TransferenciaPixAdmin(admin.ModelAdmin):
    list_display = ['transaction', 'chave_destino_valor', 'status']
    list_filter = ['status']
