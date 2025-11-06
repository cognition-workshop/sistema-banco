from django.contrib import admin
from django.utils.html import format_html

from transactions.models import Transaction
from transactions.constants import DEPOSIT, WITHDRAWAL, INTEREST


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('account', 'get_transaction_type', 'get_colored_amount', 'balance_after_transaction', 'timestamp')
    list_filter = ('transaction_type', 'timestamp')
    search_fields = ('account__account_no', 'account__user__email')
    readonly_fields = ('account', 'amount', 'transaction_type', 'balance_after_transaction', 'timestamp')
    ordering = ('-timestamp',)
    
    date_hierarchy = 'timestamp'
    
    def get_transaction_type(self, obj):
        type_map = {DEPOSIT: 'Deposit', WITHDRAWAL: 'Withdrawal', INTEREST: 'Interest'}
        return type_map.get(obj.transaction_type, 'Unknown')
    get_transaction_type.short_description = 'Type'
    
    def get_colored_amount(self, obj):
        color = 'green' if obj.transaction_type == DEPOSIT else 'red'
        return format_html('<span style="color: {};">${:.2f}</span>', color, obj.amount)
    get_colored_amount.short_description = 'Amount'
    get_colored_amount.admin_order_field = 'amount'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
