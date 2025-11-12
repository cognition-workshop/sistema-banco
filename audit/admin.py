from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'user', 'action', 'content_type', 'object_id', 'ip_address']
    list_filter = ['action', 'content_type', 'timestamp']
    search_fields = ['user__email', 'ip_address', 'content_hash']
    readonly_fields = [
        'timestamp', 'user', 'action', 'content_type', 'object_id',
        'old_value', 'new_value', 'ip_address', 'content_hash'
    ]
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions
