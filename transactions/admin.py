from django.contrib import admin

from transactions.models import Transaction, AuditLog


class AuditLogAdmin(admin.ModelAdmin):
    list_display = [
        'timestamp',
        'action_type',
        'account',
        'user',
        'amount',
        'balance_before',
        'balance_after',
    ]
    list_filter = [
        'action_type',
        'timestamp',
        'account',
    ]
    search_fields = [
        'account__account_no',
        'account__user__email',
        'user__email',
    ]
    readonly_fields = [
        'user',
        'account',
        'action_type',
        'timestamp',
        'balance_before',
        'balance_after',
        'amount',
        'transaction',
        'ip_address',
        'user_agent',
        'metadata',
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
