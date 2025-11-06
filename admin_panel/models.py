from django.db import models
from django.conf import settings
from accounts.models import UserBankAccount


class AdminPermissionGroup(models.Model):
    ADMIN = 'ADMIN'
    MANAGER = 'MANAGER'
    AUDITOR = 'AUDITOR'
    
    PERMISSION_CHOICES = [
        (ADMIN, 'Administrador - Acesso Total'),
        (MANAGER, 'Gerente - Gerenciamento de Usuários'),
        (AUDITOR, 'Auditor - Apenas Leitura'),
    ]
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='admin_permission'
    )
    permission_level = models.CharField(
        max_length=20,
        choices=PERMISSION_CHOICES,
        default=AUDITOR
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Permissão Admin'
        verbose_name_plural = 'Permissões Admin'
    
    def __str__(self):
        return f'{self.user.email} - {self.get_permission_level_display()}'
    
    def can_manage_users(self):
        return self.permission_level in [self.ADMIN, self.MANAGER]
    
    def can_view_fraud_alerts(self):
        return self.permission_level in [self.ADMIN, self.MANAGER, self.AUDITOR]
    
    def has_full_access(self):
        return self.permission_level == self.ADMIN


class UserSuspension(models.Model):
    account = models.ForeignKey(
        UserBankAccount,
        on_delete=models.CASCADE,
        related_name='suspensions'
    )
    suspended_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='suspensions_made'
    )
    reason = models.TextField()
    suspended_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    unsuspended_at = models.DateTimeField(null=True, blank=True)
    unsuspended_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='unsuspensions_made'
    )
    
    class Meta:
        verbose_name = 'Suspensão'
        verbose_name_plural = 'Suspensões'
        ordering = ['-suspended_at']
    
    def __str__(self):
        status = 'Ativa' if self.is_active else 'Removida'
        return f'Suspensão #{self.id} - Conta {self.account.account_no} ({status})'
