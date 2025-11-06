from django.contrib import admin

from transactions.models import Transaction, AuditLog


class TransactionAdmin(admin.ModelAdmin):
    list_display = ['account', 'amount', 'transaction_type', 'timestamp']
    list_filter = ['transaction_type', 'timestamp']
    search_fields = ['account__user__email', 'account__account_no']


class AuditLogAdmin(admin.ModelAdmin):
    list_display = [
        'timestamp',
        'user',
        'action_type',
        'amount',
        'balance_before',
        'balance_after',
        'ip_address'
    ]
    
    list_filter = [
        'action_type',
        'timestamp',
        ('user', admin.RelatedOnlyFieldListFilter),
    ]
    
    search_fields = [
        'user__email',
        'transaction__id',
        'action_type',
        'ip_address'
    ]
    
    readonly_fields = [
        'user',
        'transaction',
        'action_type',
        'amount',
        'balance_before',
        'balance_after',
        'timestamp',
        'ip_address',
        'user_agent',
        'metadata'
    ]
    
    ordering = ['-timestamp']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(Transaction, TransactionAdmin)
admin.site.register(AuditLog, AuditLogAdmin)
