from django.contrib import admin
from django.utils.html import format_html

from transactions.models import Transaction
from transactions.constants import DEPOSIT, WITHDRAWAL, INTEREST


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'get_account_number', 'get_user_email', 
        'get_transaction_type_display', 'get_amount_colored',
        'balance_after_transaction', 'timestamp'
    )
    list_filter = ('transaction_type', 'timestamp', 'account__account_type')
    search_fields = (
        'account__account_no', 'account__user__email',
        'account__user__first_name', 'account__user__last_name'
    )
    readonly_fields = (
        'account', 'amount', 'balance_after_transaction',
        'transaction_type', 'timestamp'
    )
    ordering = ('-timestamp',)
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def get_account_number(self, obj):
        return obj.account.account_no
    get_account_number.short_description = 'Account Number'
    get_account_number.admin_order_field = 'account__account_no'
    
    def get_user_email(self, obj):
        return obj.account.user.email
    get_user_email.short_description = 'User Email'
    get_user_email.admin_order_field = 'account__user__email'
    
    def get_transaction_type_display(self, obj):
        type_map = {DEPOSIT: 'Deposit', WITHDRAWAL: 'Withdrawal', INTEREST: 'Interest'}
        return type_map.get(obj.transaction_type, 'Unknown')
    get_transaction_type_display.short_description = 'Type'
    
    def get_amount_colored(self, obj):
        color = 'green' if obj.transaction_type == DEPOSIT else 'red' if obj.transaction_type == WITHDRAWAL else 'blue'
        return format_html('<span style="color: {};">${:,.2f}</span>', color, obj.amount)
    get_amount_colored.short_description = 'Amount'
    get_amount_colored.admin_order_field = 'amount'
