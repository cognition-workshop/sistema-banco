from django.contrib import admin
from django.core.exceptions import PermissionDenied
from .models import AuditLog, ImmutableTransaction


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'user', 'action', 'model_name', 'object_id', 'ip_address']
    list_filter = ['action', 'model_name', 'timestamp']
    search_fields = ['user__email', 'model_name', 'object_id', 'ip_address']
    readonly_fields = [
        'timestamp', 'user', 'action', 'model_name', 'object_id',
        'previous_value', 'new_value', 'ip_address', 'user_agent',
        'hash_signature', 'previous_hash'
    ]
    ordering = ['-timestamp']
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(ImmutableTransaction)
class ImmutableTransactionAdmin(admin.ModelAdmin):
    list_display = ['transaction_id', 'account_id', 'amount', 'transaction_type', 'timestamp']
    list_filter = ['transaction_type', 'timestamp']
    search_fields = ['transaction_id', 'account_id']
    readonly_fields = [
        'transaction_id', 'account_id', 'amount', 'balance_after_transaction',
        'transaction_type', 'timestamp', 'created_at', 'hash_signature',
        'previous_hash', 'digital_signature'
    ]
    ordering = ['-timestamp']
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
