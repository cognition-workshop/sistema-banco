from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['action', 'user', 'target_user', 'timestamp', 'ip_address']
    list_filter = ['action', 'timestamp']
    search_fields = ['user__email', 'target_user__email', 'description']
    readonly_fields = ['user', 'target_user', 'action', 'description', 'timestamp', 'ip_address']
