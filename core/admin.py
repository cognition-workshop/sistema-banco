from django.contrib import admin
from django.utils import timezone
from .models import FraudAlert


@admin.register(FraudAlert)
class FraudAlertAdmin(admin.ModelAdmin):
    list_display = ('alert_type', 'account', 'severity', 'status', 'created_at', 'reviewed_by')
    list_filter = ('alert_type', 'severity', 'status', 'created_at')
    search_fields = ('account__account_no', 'account__user__email', 'description')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Alert Information', {'fields': ('alert_type', 'account', 'transaction', 'severity')}),
        ('Description', {'fields': ('description',)}),
        ('Status', {'fields': ('status', 'reviewed_by', 'reviewed_at', 'notes')}),
        ('Timestamps', {'fields': ('created_at',)}),
    )
    
    actions = ['mark_as_reviewed', 'mark_as_resolved', 'mark_as_false_positive']
    
    def mark_as_reviewed(self, request, queryset):
        queryset.update(status='REVIEWED', reviewed_by=request.user, reviewed_at=timezone.now())
    mark_as_reviewed.short_description = 'Mark as Reviewed'
    
    def mark_as_resolved(self, request, queryset):
        queryset.update(status='RESOLVED', reviewed_by=request.user, reviewed_at=timezone.now())
    mark_as_resolved.short_description = 'Mark as Resolved'
    
    def mark_as_false_positive(self, request, queryset):
        queryset.update(status='FALSE_POSITIVE', reviewed_by=request.user, reviewed_at=timezone.now())
    mark_as_false_positive.short_description = 'Mark as False Positive'
