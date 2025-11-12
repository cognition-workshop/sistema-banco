from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Sum, Avg
from django.urls import path
from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta

from transactions.models import Transaction, FraudPattern, FraudAlert
from transactions.constants import DEPOSIT, WITHDRAWAL, INTEREST


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'account_link', 'transaction_type_badge', 'amount_display', 'balance_after', 'timestamp')
    list_filter = ('transaction_type', 'timestamp')
    search_fields = ('account__account_no', 'account__user__email')
    readonly_fields = ('account', 'amount', 'balance_after_transaction', 'transaction_type', 'timestamp')
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Informações da Transação', {
            'fields': ('account', 'transaction_type', 'amount', 'balance_after_transaction', 'timestamp')
        }),
    )
    
    def account_link(self, obj):
        from django.urls import reverse
        url = reverse('admin:accounts_userbankaccount_change', args=[obj.account.pk])
        return format_html('<a href="{}">{}</a>', url, obj.account.account_no)
    account_link.short_description = 'Conta'
    
    def transaction_type_badge(self, obj):
        colors = {
            DEPOSIT: 'green',
            WITHDRAWAL: 'red',
            INTEREST: 'blue'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            colors.get(obj.transaction_type, 'gray'),
            obj.get_transaction_type_display()
        )
    transaction_type_badge.short_description = 'Tipo'
    
    def amount_display(self, obj):
        return f'R$ {obj.amount:.2f}'
    amount_display.short_description = 'Valor'
    
    def balance_after(self, obj):
        return f'R$ {obj.balance_after_transaction:.2f}'
    balance_after.short_description = 'Saldo Após'
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('account', 'account__user')


@admin.register(FraudPattern)
class FraudPatternAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'alert_count', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    
    def alert_count(self, obj):
        return obj.fraudalert_set.count()
    alert_count.short_description = 'Alertas Gerados'


@admin.register(FraudAlert)
class FraudAlertAdmin(admin.ModelAdmin):
    list_display = ('id', 'account_link', 'pattern', 'severity_badge', 'status_badge', 'detected_at')
    list_filter = ('severity', 'status', 'pattern', 'detected_at')
    search_fields = ('account__account_no', 'account__user__email', 'description')
    readonly_fields = ('account', 'pattern', 'detected_at')
    date_hierarchy = 'detected_at'
    
    fieldsets = (
        ('Informações do Alerta', {
            'fields': ('account', 'pattern', 'severity', 'status', 'description')
        }),
        ('Datas', {
            'fields': ('detected_at', 'resolved_at')
        }),
        ('Notas', {
            'fields': ('notes',)
        }),
    )
    
    actions = ['mark_as_investigating', 'mark_as_resolved', 'mark_as_false_positive']
    
    def account_link(self, obj):
        from django.urls import reverse
        url = reverse('admin:accounts_userbankaccount_change', args=[obj.account.pk])
        return format_html('<a href="{}">{}</a>', url, obj.account.account_no)
    account_link.short_description = 'Conta'
    
    def severity_badge(self, obj):
        colors = {
            'LOW': '#28a745',
            'MEDIUM': '#ffc107',
            'HIGH': '#fd7e14',
            'CRITICAL': '#dc3545'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            colors.get(obj.severity, 'gray'),
            obj.get_severity_display()
        )
    severity_badge.short_description = 'Severidade'
    
    def status_badge(self, obj):
        colors = {
            'PENDING': '#6c757d',
            'INVESTIGATING': '#007bff',
            'RESOLVED': '#28a745',
            'FALSE_POSITIVE': '#17a2b8'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            colors.get(obj.status, 'gray'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def mark_as_investigating(self, request, queryset):
        updated = queryset.update(status='INVESTIGATING')
        self.message_user(request, f'{updated} alerta(s) marcado(s) como em investigação.')
    mark_as_investigating.short_description = 'Marcar como Em Investigação'
    
    def mark_as_resolved(self, request, queryset):
        queryset.update(status='RESOLVED', resolved_at=timezone.now())
        self.message_user(request, f'{queryset.count()} alerta(s) marcado(s) como resolvido(s).')
    mark_as_resolved.short_description = 'Marcar como Resolvido'
    
    def mark_as_false_positive(self, request, queryset):
        queryset.update(status='FALSE_POSITIVE', resolved_at=timezone.now())
        self.message_user(request, f'{queryset.count()} alerta(s) marcado(s) como falso positivo.')
    mark_as_false_positive.short_description = 'Marcar como Falso Positivo'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('account', 'account__user', 'pattern')
