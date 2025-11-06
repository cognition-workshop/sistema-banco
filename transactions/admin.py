from django.contrib import admin

from transactions.models import Transaction, AuditLog


admin.site.register(Transaction)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'account', 'operation_type', 'amount', 'balance_before', 'balance_after')
    list_filter = ('operation_type', 'timestamp', 'account')
    search_fields = ('account__account_no', 'user__email', 'description')
    readonly_fields = ('user', 'account', 'transaction', 'operation_type', 'amount', 
                      'balance_before', 'balance_after', 'timestamp', 'ip_address', 'description')
    ordering = ('-timestamp',)
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions
