from django.contrib import admin

from transactions.models import Transaction, AuditLog


class AuditLogAdmin(admin.ModelAdmin):
    list_display = [
        'timestamp',
        'account',
        'operation_type',
        'amount',
        'balance_before',
        'balance_after',
        'user',
        'ip_address'
    ]
    list_filter = [
        'operation_type',
        'timestamp',
        'account__account_type'
    ]
    search_fields = [
        'account__account_no',
        'account__user__email',
        'user__email',
        'ip_address'
    ]
    readonly_fields = [
        'user',
        'account',
        'operation_type',
        'amount',
        'balance_before',
        'balance_after',
        'timestamp',
        'ip_address',
        'metadata'
    ]
    ordering = ['-timestamp']
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


admin.site.register(Transaction)
admin.site.register(AuditLog, AuditLogAdmin)
