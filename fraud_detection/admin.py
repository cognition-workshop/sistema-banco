from django.contrib import admin
from .models import FraudAlert


@admin.register(FraudAlert)
class FraudAlertAdmin(admin.ModelAdmin):
    list_display = ['alert_type', 'account', 'severity', 'status', 'created_at']
    list_filter = ['severity', 'status', 'created_at']
    search_fields = ['account__account_no', 'account__user__email', 'message']
    readonly_fields = ['created_at']
