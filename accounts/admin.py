from django.contrib import admin
from django.utils import timezone

from .models import BankAccountType, User, UserAddress, UserBankAccount, FraudRule, SuspiciousTransaction


admin.site.register(BankAccountType)
admin.site.register(User)
admin.site.register(UserAddress)
admin.site.register(UserBankAccount)


@admin.register(FraudRule)
class FraudRuleAdmin(admin.ModelAdmin):
    list_display = ['rule_type', 'severity', 'is_active', 'created_at']
    list_filter = ['rule_type', 'severity', 'is_active']
    search_fields = ['rule_type']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('rule_type', 'severity', 'is_active')
        }),
        ('Parameters', {
            'fields': ('parameters',),
            'description': 'Rule-specific parameters in JSON format. Examples:\n'
                          '- High Value: {"threshold": 10000}\n'
                          '- High Frequency: {"count": 5, "window_minutes": 10}\n'
                          '- Unusual Hours: {"start_hour": 2, "end_hour": 5}\n'
                          '- Pattern Change: {"deviation_multiplier": 3}'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SuspiciousTransaction)
class SuspiciousTransactionAdmin(admin.ModelAdmin):
    list_display = ['transaction', 'status', 'detected_at', 'reviewed_by']
    list_filter = ['status', 'detected_at']
    search_fields = ['transaction__account__account_no', 'notes']
    readonly_fields = ['transaction', 'detected_at', 'fraud_rules']
    filter_horizontal = ['fraud_rules']
    
    fieldsets = (
        ('Transaction Details', {
            'fields': ('transaction', 'fraud_rules', 'detected_at')
        }),
        ('Review', {
            'fields': ('status', 'reviewed_by', 'reviewed_at', 'notes')
        }),
    )
    
    actions = ['approve_transactions', 'reject_transactions']
    
    def approve_transactions(self, request, queryset):
        count = queryset.filter(status=SuspiciousTransaction.PENDING).update(
            status=SuspiciousTransaction.APPROVED,
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )
        self.message_user(request, f'{count} transaction(s) approved.')
    approve_transactions.short_description = 'Approve selected suspicious transactions'
    
    def reject_transactions(self, request, queryset):
        count = queryset.filter(status=SuspiciousTransaction.PENDING).update(
            status=SuspiciousTransaction.REJECTED,
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )
        self.message_user(request, f'{count} transaction(s) rejected.')
    reject_transactions.short_description = 'Reject selected suspicious transactions'
    
    def has_change_permission(self, request, obj=None):
        return request.user.has_perm('accounts.can_review_suspicious_transactions')
    
    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm('accounts.can_review_suspicious_transactions')
