from django.contrib import admin
from .models import FraudRule, FraudAlert


@admin.register(FraudRule)
class FraudRuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'rule_type', 'severity', 'is_active', 'created_at']
    list_filter = ['rule_type', 'severity', 'is_active']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(FraudAlert)
class FraudAlertAdmin(admin.ModelAdmin):
    list_display = ['id', 'transaction', 'rule', 'severity', 'status', 'created_at']
    list_filter = ['severity', 'status', 'created_at']
    search_fields = ['description']
    readonly_fields = ['created_at']
    raw_id_fields = ['transaction', 'rule', 'account', 'resolved_by']
