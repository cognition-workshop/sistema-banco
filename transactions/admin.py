from django.contrib import admin

from transactions.models import Transaction


class TransactionAdmin(admin.ModelAdmin):
    list_display = ['id', 'account', 'transaction_type', 'amount', 'balance_after_transaction', 'timestamp']
    list_filter = ['transaction_type', 'timestamp']
    search_fields = ['account__account_no', 'account__user__email']
    readonly_fields = ['account', 'amount', 'balance_after_transaction', 'transaction_type', 'timestamp']
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions


admin.site.register(Transaction, TransactionAdmin)
