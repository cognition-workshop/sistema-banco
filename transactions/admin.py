from django.contrib import admin
from django.db.models import Sum, Count, Q
from django.utils.html import format_html
from django.urls import reverse
from datetime import timedelta
from django.utils import timezone

from transactions.models import Transaction
from transactions.constants import DEPOSIT, WITHDRAWAL, INTEREST


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['id', 'account_link', 'user_email', 'transaction_type_display', 'amount_display', 'balance_after', 'timestamp', 'fraud_flag']
    list_filter = ['transaction_type', 'timestamp']
    search_fields = ['account__account_no', 'account__user__email', 'account__user__first_name', 'account__user__last_name']
    readonly_fields = ['timestamp', 'fraud_check_details']
    date_hierarchy = 'timestamp'
    ordering = ['-timestamp']
    actions = ['flag_as_fraud', 'approve_transactions', 'export_to_csv']
    
    def account_link(self, obj):
        url = reverse('admin:accounts_userbankaccount_change', args=[obj.account.id])
        return format_html('<a href="{}">{}</a>', url, obj.account.account_no)
    account_link.short_description = 'Account'
    
    def user_email(self, obj):
        return obj.account.user.email
    user_email.short_description = 'User Email'
    user_email.admin_order_field = 'account__user__email'
    
    def transaction_type_display(self, obj):
        type_colors = {DEPOSIT: 'green', WITHDRAWAL: 'red', INTEREST: 'blue'}
        type_names = {DEPOSIT: 'Deposit', WITHDRAWAL: 'Withdrawal', INTEREST: 'Interest'}
        color = type_colors.get(obj.transaction_type, 'black')
        name = type_names.get(obj.transaction_type, 'Unknown')
        return format_html('<span style="color: {};">{}</span>', color, name)
    transaction_type_display.short_description = 'Type'
    
    def amount_display(self, obj):
        return f'${obj.amount:.2f}'
    amount_display.short_description = 'Amount'
    amount_display.admin_order_field = 'amount'
    
    def balance_after(self, obj):
        return f'${obj.balance_after_transaction:.2f}'
    balance_after.short_description = 'Balance After'
    
    def fraud_flag(self, obj):
        if self._is_suspicious(obj):
            return format_html('<span style="color: red; font-weight: bold;">⚠️ SUSPICIOUS</span>')
        return format_html('<span style="color: green;">✓</span>')
    fraud_flag.short_description = 'Fraud Check'
    
    def fraud_check_details(self, obj):
        reasons = []
        
        if obj.transaction_type == WITHDRAWAL and obj.amount > obj.account.account_type.maximum_withdrawal_amount:
            reasons.append(f"Exceeds maximum withdrawal limit (${obj.account.account_type.maximum_withdrawal_amount:.2f})")
        
        if obj.amount > 50000:
            reasons.append(f"Large transaction amount (${obj.amount:.2f})")
        
        recent_transactions = Transaction.objects.filter(
            account=obj.account,
            timestamp__gte=obj.timestamp - timedelta(hours=1),
            timestamp__lte=obj.timestamp
        ).exclude(id=obj.id).count()
        
        if recent_transactions >= 5:
            reasons.append(f"Multiple transactions in short time ({recent_transactions} in last hour)")
        
        if reasons:
            return format_html('<br>'.join([f'• {r}' for r in reasons]))
        return "No suspicious activity detected"
    fraud_check_details.short_description = 'Fraud Detection Details'
    
    def _is_suspicious(self, obj):
        if obj.transaction_type == WITHDRAWAL and obj.amount > obj.account.account_type.maximum_withdrawal_amount:
            return True
        
        if obj.amount > 50000:
            return True
        
        recent_count = Transaction.objects.filter(
            account=obj.account,
            timestamp__gte=obj.timestamp - timedelta(hours=1),
            timestamp__lte=obj.timestamp
        ).exclude(id=obj.id).count()
        
        if recent_count >= 5:
            return True
        
        return False
    
    @admin.action(description='Flag as fraud')
    def flag_as_fraud(self, request, queryset):
        self.message_user(request, f'{queryset.count()} transaction(s) flagged for review.')
    
    @admin.action(description='Approve transactions')
    def approve_transactions(self, request, queryset):
        self.message_user(request, f'{queryset.count()} transaction(s) approved.')
    
    @admin.action(description='Export to CSV')
    def export_to_csv(self, request, queryset):
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="transactions.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['ID', 'Account', 'User Email', 'Type', 'Amount', 'Balance After', 'Timestamp'])
        
        for transaction in queryset:
            type_names = {DEPOSIT: 'Deposit', WITHDRAWAL: 'Withdrawal', INTEREST: 'Interest'}
            writer.writerow([
                transaction.id,
                transaction.account.account_no,
                transaction.account.user.email,
                type_names.get(transaction.transaction_type, 'Unknown'),
                transaction.amount,
                transaction.balance_after_transaction,
                transaction.timestamp,
            ])
        
        return response
