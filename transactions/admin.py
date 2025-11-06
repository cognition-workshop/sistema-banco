from django.contrib import admin

from transactions.models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'account',
        'transaction_type',
        'amount',
        'balance_before_transaction',
        'balance_after_transaction',
        'user',
        'ip_address',
        'timestamp',
    ]
    list_filter = ['transaction_type', 'timestamp']
    search_fields = ['account__account_no', 'user__email', 'ip_address']
    readonly_fields = [
        'account',
        'amount',
        'balance_before_transaction',
        'balance_after_transaction',
        'transaction_type',
        'timestamp',
        'user',
        'ip_address',
    ]
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        return True
