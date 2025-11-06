from django.contrib import admin

from transactions.models import Transaction


class TransactionAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'get_account_number',
        'get_user_email',
        'transaction_type',
        'amount',
        'balance_after_transaction',
        'timestamp',
    ]
    
    list_filter = [
        'transaction_type',
        'timestamp',
    ]
    
    search_fields = [
        'account__account_no',
        'account__user__email',
        'account__user__first_name',
        'account__user__last_name',
    ]
    
    date_hierarchy = 'timestamp'
    
    list_per_page = 50
    
    ordering = ['-timestamp']
    
    readonly_fields = [
        'account',
        'amount',
        'balance_after_transaction',
        'transaction_type',
        'timestamp',
    ]
    
    def get_account_number(self, obj):
        return obj.account.account_no
    get_account_number.short_description = 'Número da Conta'
    get_account_number.admin_order_field = 'account__account_no'
    
    def get_user_email(self, obj):
        return obj.account.user.email
    get_user_email.short_description = 'Email do Usuário'
    get_user_email.admin_order_field = 'account__user__email'


admin.site.register(Transaction, TransactionAdmin)
