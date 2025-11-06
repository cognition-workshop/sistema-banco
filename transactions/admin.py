from django.contrib import admin

from transactions.models import Transaction, AuditLog


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['account', 'transaction_type', 'amount', 'balance_after_transaction', 'timestamp']
    list_filter = ['transaction_type', 'timestamp']
    search_fields = ['account__account_no', 'account__user__email']
    readonly_fields = ['timestamp']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'user', 'account', 'operation_type', 'amount', 'balance_before', 'balance_after']
    list_filter = ['operation_type', 'timestamp']
    search_fields = ['user__email', 'account__account_no', 'ip_address']
    readonly_fields = [
        'user', 'account', 'operation_type', 'amount', 
        'balance_before', 'balance_after', 'timestamp', 
        'ip_address', 'user_agent', 'transaction'
    ]
    date_hierarchy = 'timestamp'
    ordering = ['-timestamp']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions
