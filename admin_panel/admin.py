from django.contrib import admin
from .models import FraudAlert, SystemHealthLog


@admin.register(FraudAlert)
class FraudAlertAdmin(admin.ModelAdmin):
    list_display = ['id', 'transaction', 'rule_triggered', 'severity', 'status', 'created_at']
    list_filter = ['status', 'severity', 'rule_triggered']
    search_fields = ['transaction__account__user__email']


@admin.register(SystemHealthLog)
class SystemHealthLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'celery_workers_active', 'redis_connected', 'cpu_usage', 'memory_usage']
    list_filter = ['redis_connected']
    ordering = ['-timestamp']
