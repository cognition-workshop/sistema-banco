from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from accounts.models import User, UserBankAccount, UserAddress, BankAccountType
from transactions.models import Transaction


class Command(BaseCommand):
    help = 'Setup permission groups for the banking system'

    def handle(self, *args, **kwargs):
        models = [User, UserBankAccount, UserAddress, BankAccountType, Transaction]
        
        admin_group, _ = Group.objects.get_or_create(name='Admin')
        supervisor_group, _ = Group.objects.get_or_create(name='Supervisor')
        auditor_group, _ = Group.objects.get_or_create(name='Auditor')

        admin_group.permissions.clear()
        supervisor_group.permissions.clear()
        auditor_group.permissions.clear()

        for model in models:
            content_type = ContentType.objects.get_for_model(model)
            permissions = Permission.objects.filter(content_type=content_type)
            admin_group.permissions.add(*permissions)

        for model in models:
            content_type = ContentType.objects.get_for_model(model)
            permissions = Permission.objects.filter(
                content_type=content_type,
                codename__in=[
                    f'add_{model._meta.model_name}',
                    f'change_{model._meta.model_name}',
                    f'view_{model._meta.model_name}',
                ]
            )
            supervisor_group.permissions.add(*permissions)

        for model in models:
            content_type = ContentType.objects.get_for_model(model)
            permissions = Permission.objects.filter(
                content_type=content_type,
                codename=f'view_{model._meta.model_name}'
            )
            auditor_group.permissions.add(*permissions)

        self.stdout.write(
            self.style.SUCCESS(
                'Successfully created groups and assigned permissions:\n'
                f'- Admin: {admin_group.permissions.count()} permissions\n'
                f'- Supervisor: {supervisor_group.permissions.count()} permissions\n'
                f'- Auditor: {auditor_group.permissions.count()} permissions'
            )
        )
