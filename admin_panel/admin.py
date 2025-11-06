from django.contrib import admin
from .models import AdminUser, AuditLog, FraudRule, FraudAlert, SystemHealthMetric


@admin.register(AdminUser)
class AdminUserAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'is_admin_active', 'created_at']
    list_filter = ['role', 'is_admin_active']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['admin_user', 'action_type', 'target_model', 'timestamp']
    list_filter = ['action_type', 'target_model', 'timestamp']
    search_fields = ['admin_user__user__email', 'target_model']
    readonly_fields = ['admin_user', 'action_type', 'target_model', 'target_id', 'details', 'timestamp', 'ip_address']


@admin.register(FraudRule)
class FraudRuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'rule_type', 'is_active', 'severity', 'created_at']
    list_filter = ['rule_type', 'is_active', 'severity']
    search_fields = ['name']


@admin.register(FraudAlert)
class FraudAlertAdmin(admin.ModelAdmin):
    list_display = ['id', 'transaction', 'rule', 'status', 'detected_at', 'reviewed_by']
    list_filter = ['status', 'detected_at']
    search_fields = ['transaction__account__account_no']
    readonly_fields = ['transaction', 'rule', 'detected_at']


@admin.register(SystemHealthMetric)
class SystemHealthMetricAdmin(admin.ModelAdmin):
    list_display = ['metric_type', 'value', 'status', 'timestamp']
    list_filter = ['metric_type', 'status', 'timestamp']
    readonly_fields = ['metric_type', 'value', 'details', 'timestamp', 'status']
