import hashlib
import json
from django.db import models
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey


class AuditLog(models.Model):
    ACTION_CREATE = 'CREATE'
    ACTION_UPDATE = 'UPDATE'
    ACTION_DELETE = 'DELETE'
    
    ACTION_CHOICES = [
        (ACTION_CREATE, 'Create'),
        (ACTION_UPDATE, 'Update'),
        (ACTION_DELETE, 'Delete'),
    ]
    
    timestamp = models.DateTimeField(db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text='User who performed the action'
    )
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    old_value = models.JSONField(null=True, blank=True, help_text='Previous values')
    new_value = models.JSONField(null=True, blank=True, help_text='New values')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    content_hash = models.CharField(max_length=64, unique=True, db_index=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        permissions = []
        default_permissions = ('add', 'view')
    
    def __str__(self):
        return f"{self.action} on {self.content_type} at {self.timestamp}"
    
    def save(self, *args, **kwargs):
        if not self.content_hash:
            if not self.timestamp:
                from django.utils import timezone
                self.timestamp = timezone.now()
            self.content_hash = self.calculate_hash()
        super().save(*args, **kwargs)
    
    def calculate_hash(self):
        previous_log = AuditLog.objects.order_by('-timestamp').first()
        previous_hash = previous_log.content_hash if previous_log else '0' * 64
        
        hash_data = {
            'timestamp': self.timestamp.isoformat() if self.timestamp else '',
            'user_id': self.user_id,
            'action': self.action,
            'content_type_id': self.content_type_id,
            'object_id': self.object_id,
            'old_value': self.old_value,
            'new_value': self.new_value,
            'ip_address': self.ip_address,
            'previous_hash': previous_hash,
        }
        
        hash_string = json.dumps(hash_data, sort_keys=True, default=str)
        return hashlib.sha256(hash_string.encode()).hexdigest()
