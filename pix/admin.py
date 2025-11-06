from django.contrib import admin
from .models import PixKey, PixTransaction, PixQRCode


@admin.register(PixKey)
class PixKeyAdmin(admin.ModelAdmin):
    list_display = ['key_type', 'key_value', 'account', 'is_active', 'created_at']
    list_filter = ['key_type', 'is_active']
    search_fields = ['key_value']


@admin.register(PixTransaction)
class PixTransactionAdmin(admin.ModelAdmin):
    list_display = ['end_to_end_id', 'sender_account', 'receiver_account', 'transaction', 'created_at']
    search_fields = ['end_to_end_id']


@admin.register(PixQRCode)
class PixQRCodeAdmin(admin.ModelAdmin):
    list_display = ['pix_key', 'amount', 'is_active', 'created_at']
    list_filter = ['is_active']
