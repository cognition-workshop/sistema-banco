from django.contrib import admin
from transactions.models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'account',
        'user',
        'transaction_type',
        'amount',
        'balance_before_transaction',
        'balance_after_transaction',
        'timestamp',
    ]
    list_filter = [
        'transaction_type',
        'timestamp',
        'user',
    ]
    search_fields = [
        'account__account_no',
        'account__user__email',
        'user__email',
        'amount',
    ]
    readonly_fields = [
        'account',
        'user',
        'transaction_type',
        'amount',
        'balance_before_transaction',
        'balance_after_transaction',
        'timestamp',
    ]
    ordering = ['-timestamp']
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
