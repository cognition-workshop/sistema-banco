from django.contrib import admin

from transactions.models import Transaction


class TransactionAdmin(admin.ModelAdmin):
    list_display = ['account', 'transaction_type', 'amount', 'timestamp', 'ip_address']
    readonly_fields = ['integrity_hash', 'timestamp']
    search_fields = ['account__account_no', 'account__user__email']
    
    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(Transaction, TransactionAdmin)
