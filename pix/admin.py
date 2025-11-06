from django.contrib import admin
from .models import PixKey, PixTransaction


@admin.register(PixKey)
class PixKeyAdmin(admin.ModelAdmin):
    list_display = ['key_type', 'key_value', 'account', 'is_active', 'created_at']
    list_filter = ['key_type', 'is_active', 'created_at']
    search_fields = ['key_value', 'account__account_no']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(PixTransaction)
class PixTransactionAdmin(admin.ModelAdmin):
    list_display = ['transaction_id', 'sender_account', 'receiver_key', 'amount', 'status', 'created_at']
    list_filter = ['status', 'created_at', 'channel']
    search_fields = ['transaction_id', 'sender_account__account_no', 'receiver_key__key_value']
    readonly_fields = ['transaction_id', 'created_at', 'completed_at', 'qr_code']
