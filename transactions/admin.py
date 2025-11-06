from django.contrib import admin

from transactions.models import Transaction, AuditLog


admin.site.register(Transaction)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'user', 'account', 'action_type', 'amount', 'balance_before', 'balance_after']
    list_filter = ['action_type', 'timestamp']
    search_fields = ['user__email', 'account__account_no']
    readonly_fields = ['user', 'account', 'transaction', 'action_type', 'amount', 'balance_before', 'balance_after', 'timestamp']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
