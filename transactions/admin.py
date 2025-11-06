from django.contrib import admin

from transactions.models import Transaction


class TransactionAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'get_account_number',
        'get_user_email',
        'amount',
        'transaction_type',
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
    ]
    date_hierarchy = 'timestamp'
    list_per_page = 50
    
    def get_account_number(self, obj):
        return obj.account.account_no
    get_account_number.short_description = 'Account Number'
    
    def get_user_email(self, obj):
        return obj.account.user.email
    get_user_email.short_description = 'User Email'


admin.site.register(Transaction, TransactionAdmin)
