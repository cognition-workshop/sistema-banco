from django.contrib import admin
from .models import Transaction, AuditLog


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['account', 'transaction_type', 'amount', 'balance_after_transaction', 'timestamp']
    list_filter = ['transaction_type', 'timestamp']
    search_fields = ['account__account_no', 'account__user__email']
    readonly_fields = ['timestamp']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = [
        'timestamp',
        'action_type',
        'account',
        'user',
        'amount',
        'balance_before',
        'balance_after',
        'ip_address'
    ]
    list_filter = ['action_type', 'timestamp']
    search_fields = [
        'account__account_no',
        'account__user__email',
        'user__email',
        'ip_address'
    ]
    readonly_fields = [
        'user', 'account', 'action_type', 'amount',
        'balance_before', 'balance_after', 'timestamp',
        'ip_address', 'user_agent', 'metadata'
    ]
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
