from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Q
from .models import Transaction
from .constants import DEPOSIT, WITHDRAWAL, INTEREST


class TransactionTypeFilter(admin.SimpleListFilter):
    title = 'transaction type'
    parameter_name = 'transaction_type'
    
    def lookups(self, request, model_admin):
        return (
            (DEPOSIT, 'Deposit'),
            (WITHDRAWAL, 'Withdrawal'),
            (INTEREST, 'Interest'),
        )
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(transaction_type=self.value())
        return queryset


class AmountRangeFilter(admin.SimpleListFilter):
    title = 'amount range'
    parameter_name = 'amount_range'
    
    def lookups(self, request, model_admin):
        return (
            ('0-100', '$0 - $100'),
            ('100-500', '$100 - $500'),
            ('500-1000', '$500 - $1,000'),
            ('1000+', '$1,000+'),
        )
    
    def queryset(self, request, queryset):
        if self.value() == '0-100':
            return queryset.filter(amount__gte=0, amount__lte=100)
        elif self.value() == '100-500':
            return queryset.filter(amount__gt=100, amount__lte=500)
        elif self.value() == '500-1000':
            return queryset.filter(amount__gt=500, amount__lte=1000)
        elif self.value() == '1000+':
            return queryset.filter(amount__gt=1000)
        return queryset


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'account_number', 'user_email', 'transaction_type_display', 
                    'amount_display', 'balance_after', 'timestamp')
    list_filter = (TransactionTypeFilter, AmountRangeFilter, 'timestamp')
    search_fields = ('account__account_no', 'account__user__email', 'account__user__first_name', 
                     'account__user__last_name')
    readonly_fields = ('timestamp', 'balance_after_transaction')
    date_hierarchy = 'timestamp'
    list_per_page = 50
    
    fieldsets = (
        ('Transaction Details', {'fields': ('account', 'transaction_type', 'amount')}),
        ('Balance Information', {'fields': ('balance_after_transaction',)}),
        ('Timestamp', {'fields': ('timestamp',)}),
    )
    
    def transaction_id(self, obj):
        return f"TXN-{obj.id:06d}"
    transaction_id.short_description = 'Transaction ID'
    
    def account_number(self, obj):
        return obj.account.account_no
    account_number.short_description = 'Account Number'
    account_number.admin_order_field = 'account__account_no'
    
    def user_email(self, obj):
        return obj.account.user.email
    user_email.short_description = 'User Email'
    user_email.admin_order_field = 'account__user__email'
    
    def transaction_type_display(self, obj):
        colors = {DEPOSIT: 'green', WITHDRAWAL: 'red', INTEREST: 'blue'}
        types = {DEPOSIT: 'Deposit', WITHDRAWAL: 'Withdrawal', INTEREST: 'Interest'}
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.transaction_type, 'black'),
            types.get(obj.transaction_type, 'Unknown')
        )
    transaction_type_display.short_description = 'Type'
    
    def amount_display(self, obj):
        return f"${obj.amount:,.2f}"
    amount_display.short_description = 'Amount'
    amount_display.admin_order_field = 'amount'
    
    def balance_after(self, obj):
        return f"${obj.balance_after_transaction:,.2f}"
    balance_after.short_description = 'Balance After'
