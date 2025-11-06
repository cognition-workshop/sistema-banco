from django.contrib import admin
from django.utils.html import format_html

from .models import Transaction, FraudAlert


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['account_no', 'transaction_type_display', 'amount', 'balance_after_transaction', 'timestamp']
    list_filter = ['transaction_type', 'timestamp']
    search_fields = ['account__account_no', 'account__user__email']
    readonly_fields = ['account', 'amount', 'balance_after_transaction', 'transaction_type', 'timestamp']
    date_hierarchy = 'timestamp'
    
    def account_no(self, obj):
        return obj.account.account_no
    account_no.short_description = 'Account Number'
    
    def transaction_type_display(self, obj):
        colors = {1: 'green', 2: 'red', 3: 'blue'}
        return format_html(
            '<span style="color: {};">{}</span>',
            colors.get(obj.transaction_type, 'black'),
            obj.get_transaction_type_display()
        )
    transaction_type_display.short_description = 'Type'


@admin.register(FraudAlert)
class FraudAlertAdmin(admin.ModelAdmin):
    list_display = ['account_no', 'alert_type', 'severity', 'is_resolved', 'created_at']
    list_filter = ['alert_type', 'severity', 'is_resolved', 'created_at']
    search_fields = ['account__account_no', 'account__user__email', 'description']
    readonly_fields = ['account', 'alert_type', 'severity', 'description', 'transaction', 'created_at']
    date_hierarchy = 'created_at'
    actions = ['mark_resolved', 'mark_unresolved']
    
    def account_no(self, obj):
        return obj.account.account_no
    account_no.short_description = 'Account Number'
    
    def mark_resolved(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(is_resolved=True, resolved_at=timezone.now())
        self.message_user(request, f'{updated} alert(s) marked as resolved.')
    mark_resolved.short_description = 'Mark selected alerts as resolved'
    
    def mark_unresolved(self, request, queryset):
        updated = queryset.update(is_resolved=False, resolved_at=None)
        self.message_user(request, f'{updated} alert(s) marked as unresolved.')
    mark_unresolved.short_description = 'Mark selected alerts as unresolved'
