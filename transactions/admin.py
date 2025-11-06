from django.contrib import admin
from .models import Transaction, FailedTransaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['account', 'amount', 'transaction_type', 'timestamp', 'ip_address', 'channel']
    list_filter = ['transaction_type', 'timestamp', 'channel']
    search_fields = ['account__account_no', 'ip_address']
    readonly_fields = ['timestamp', 'hash_signature', 'ip_address', 'geolocation', 'channel']


@admin.register(FailedTransaction)
class FailedTransactionAdmin(admin.ModelAdmin):
    list_display = ['account', 'amount', 'transaction_type', 'timestamp', 'error_code', 'ip_address']
    list_filter = ['transaction_type', 'timestamp', 'error_code']
    search_fields = ['account__account_no', 'error_message', 'ip_address']
    readonly_fields = ['timestamp', 'ip_address', 'geolocation', 'channel', 'error_message', 'error_code']
