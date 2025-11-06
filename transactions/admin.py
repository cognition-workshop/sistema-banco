from django.contrib import admin

from transactions.models import Transaction, AuditLog


class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'user', 'account', 'operation_type', 'amount', 'balance_before', 'balance_after']
    list_filter = ['operation_type', 'timestamp']
    search_fields = ['user__email', 'account__account_no', 'description']
    readonly_fields = ['user', 'account', 'transaction', 'operation_type', 'amount', 'balance_before', 'balance_after', 'timestamp', 'description']
    ordering = ['-timestamp']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(Transaction)
admin.site.register(AuditLog, AuditLogAdmin)
