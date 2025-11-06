from django.contrib import admin
from django.utils.html import format_html

from .models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['account_no', 'transaction_type_display', 'amount_display', 'balance_after_display', 'timestamp']
    list_filter = ['transaction_type', 'timestamp']
    search_fields = ['account__account_no', 'account__user__email']
    readonly_fields = ['account', 'amount', 'balance_after_transaction', 'transaction_type', 'timestamp']
    date_hierarchy = 'timestamp'
    
    def account_no(self, obj):
        return obj.account.account_no
    account_no.short_description = 'Conta'
    account_no.admin_order_field = 'account__account_no'
    
    def transaction_type_display(self, obj):
        color = 'green' if obj.transaction_type == 1 else 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_transaction_type_display()
        )
    transaction_type_display.short_description = 'Tipo'
    transaction_type_display.admin_order_field = 'transaction_type'
    
    def amount_display(self, obj):
        color = 'green' if obj.transaction_type == 1 else 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">R$ {}</span>',
            color,
            f'{obj.amount:,.2f}'
        )
    amount_display.short_description = 'Valor'
    amount_display.admin_order_field = 'amount'
    
    def balance_after_display(self, obj):
        return format_html(
            '<span style="font-weight: bold;">R$ {}</span>',
            f'{obj.balance_after_transaction:,.2f}'
        )
    balance_after_display.short_description = 'Saldo Após'
    balance_after_display.admin_order_field = 'balance_after_transaction'
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
