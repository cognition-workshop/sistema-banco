from django.contrib import admin
from .models import FraudAlert


@admin.register(FraudAlert)
class FraudAlertAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'rule_triggered', 'severity', 'status', 'created_at']
    list_filter = ['severity', 'status', 'rule_triggered']
    search_fields = ['user__email', 'description']
    readonly_fields = ['created_at']
