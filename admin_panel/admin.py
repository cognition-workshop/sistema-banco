from django.contrib import admin
from .models import FraudRule, FraudAlert, AdminAuditLog, AccountWhitelist


@admin.register(FraudRule)
class FraudRuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'rule_type', 'is_active', 'created_at']
    list_filter = ['rule_type', 'is_active']
    search_fields = ['name', 'description']


@admin.register(FraudAlert)
class FraudAlertAdmin(admin.ModelAdmin):
    list_display = ['account', 'severity', 'status', 'created_at']
    list_filter = ['severity', 'status']
    search_fields = ['account__account_no', 'description']


@admin.register(AdminAuditLog)
class AdminAuditLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'timestamp']
    list_filter = ['timestamp']
    search_fields = ['user__email', 'action']


@admin.register(AccountWhitelist)
class AccountWhitelistAdmin(admin.ModelAdmin):
    list_display = ['account', 'added_by', 'created_at']
    search_fields = ['account__account_no', 'reason']
