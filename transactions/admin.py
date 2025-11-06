from django.contrib import admin
from .models import Transaction, AuditLog


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['id', 'account', 'transaction_type', 'amount', 'balance_after_transaction', 'timestamp']
    list_filter = ['transaction_type', 'timestamp']
    search_fields = ['account__account_no', 'account__user__email']
    readonly_fields = ['timestamp']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'action_type', 'user', 'success', 'amount', 'ip_address', 'timestamp']
    list_filter = ['action_type', 'success', 'timestamp']
    search_fields = ['user__email', 'ip_address', 'error_message']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Action Information', {
            'fields': ('action_type', 'success', 'error_message')
        }),
        ('User Information', {
            'fields': ('user', 'ip_address', 'user_agent')
        }),
        ('Transaction Details', {
            'fields': ('transaction', 'amount', 'additional_data')
        }),
        ('Metadata', {
            'fields': ('timestamp',)
        }),
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
