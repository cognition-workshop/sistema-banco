from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from accounts.models import User


class Command(BaseCommand):
    help = 'Setup admin portal permissions and groups'

    def handle(self, *args, **kwargs):
        user_ct = ContentType.objects.get_for_model(User)
        
        permissions = [
            ('view_all_users', 'Can view all users'),
            ('edit_user_details', 'Can edit user details'),
            ('suspend_user', 'Can suspend/activate users'),
            ('view_all_transactions', 'Can view all transactions'),
            ('export_data', 'Can export data'),
            ('view_fraud_alerts', 'Can view fraud alerts'),
            ('review_fraud_alerts', 'Can review fraud alerts'),
            ('view_system_health', 'Can view system health'),
        ]
        
        for codename, name in permissions:
            Permission.objects.get_or_create(
                codename=codename,
                name=name,
                content_type=user_ct,
            )
        
        viewer_group, _ = Group.objects.get_or_create(name='Admin Viewer')
        viewer_perms = ['view_all_users', 'view_all_transactions', 'view_fraud_alerts', 'view_system_health']
        for perm_code in viewer_perms:
            perm = Permission.objects.get(codename=perm_code)
            viewer_group.permissions.add(perm)
        
        manager_group, _ = Group.objects.get_or_create(name='Admin Manager')
        manager_perms = viewer_perms + ['edit_user_details', 'suspend_user', 'export_data', 'review_fraud_alerts']
        for perm_code in manager_perms:
            perm = Permission.objects.get(codename=perm_code)
            manager_group.permissions.add(perm)
        
        self.stdout.write(self.style.SUCCESS('Successfully setup admin permissions'))
