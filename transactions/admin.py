from django.contrib import admin
from transactions.models import Transaction, PIXKey, PIXTransaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['id', 'account', 'amount', 'transaction_type', 'timestamp']
    list_filter = ['transaction_type', 'timestamp']
    search_fields = ['account__user__email', 'account__user__cpf']
    readonly_fields = ['timestamp', 'balance_after_transaction']
    ordering = ['-timestamp']


@admin.register(PIXKey)
class PIXKeyAdmin(admin.ModelAdmin):
    list_display = ['user', 'key_type', 'key_value', 'is_active', 'created_at']
    list_filter = ['key_type', 'is_active', 'created_at']
    search_fields = ['user__email', 'user__cpf', 'key_value']
    readonly_fields = ['created_at']
    ordering = ['-created_at']


@admin.register(PIXTransaction)
class PIXTransactionAdmin(admin.ModelAdmin):
    list_display = ['transaction', 'e2e_id', 'pix_key_used', 'created_at']
    list_filter = ['created_at']
    search_fields = ['e2e_id', 'pix_key_used']
    readonly_fields = ['transaction', 'e2e_id', 'payer_info', 'payee_info', 'pix_key_used', 'created_at']
    ordering = ['-created_at']
