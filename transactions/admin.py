from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum, Count, Q
from django.http import HttpResponse
import csv
from datetime import datetime, timedelta

from transactions.models import Transaction
from transactions.constants import DEPOSIT, WITHDRAWAL, INTEREST


class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'account_number', 'transaction_type_display', 
                   'amount_display', 'balance_after_display', 'timestamp')
    list_filter = ('transaction_type', 'timestamp', 'account__account_type')
    search_fields = ('account__account_no', 'account__user__email')
    date_hierarchy = 'timestamp'
    ordering = ('-timestamp',)
    
    fieldsets = (
        ('Transaction Information', {
            'fields': ('account', 'transaction_type', 'amount')
        }),
        ('Audit Information', {
            'fields': ('balance_after_transaction', 'timestamp'),
            'description': 'Read-only audit fields'
        }),
    )
    
    readonly_fields = ('balance_after_transaction', 'timestamp')
    
    actions = ['export_as_csv', 'flag_for_review']
    
    @admin.display(description='Account Number', ordering='account__account_no')
    def account_number(self, obj):
        return obj.account.account_no
    
    @admin.display(description='Type', ordering='transaction_type')
    def transaction_type_display(self, obj):
        colors = {
            DEPOSIT: 'green',
            WITHDRAWAL: 'red',
            INTEREST: 'blue'
        }
        names = {
            DEPOSIT: 'Deposit',
            WITHDRAWAL: 'Withdrawal',
            INTEREST: 'Interest'
        }
        color = colors.get(obj.transaction_type, 'black')
        name = names.get(obj.transaction_type, 'Unknown')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, name
        )
    
    @admin.display(description='Amount', ordering='amount')
    def amount_display(self, obj):
        color = 'green' if obj.transaction_type == DEPOSIT else 'red'
        prefix = '+' if obj.transaction_type in [DEPOSIT, INTEREST] else '-'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} ${:,.2f}</span>',
            color, prefix, obj.amount
        )
    
    @admin.display(description='Balance After', ordering='balance_after_transaction')
    def balance_after_display(self, obj):
        return f'${obj.balance_after_transaction:,.2f}'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('account', 'account__user', 'account__account_type')
    
    @admin.action(description='Export selected transactions as CSV')
    def export_as_csv(self, request, queryset):
        meta = self.model._meta
        field_names = ['id', 'account', 'transaction_type', 'amount', 
                      'balance_after_transaction', 'timestamp']
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename={meta.verbose_name_plural}.csv'
        writer = csv.writer(response)
        
        writer.writerow(field_names)
        for obj in queryset:
            writer.writerow([getattr(obj, field) for field in field_names])
        
        return response
    
    @admin.action(description='Flag transactions for compliance review')
    def flag_for_review(self, request, queryset):
        count = queryset.count()
        self.message_user(
            request,
            f'{count} transaction(s) flagged for compliance review.'
        )


admin.site.register(Transaction, TransactionAdmin)
