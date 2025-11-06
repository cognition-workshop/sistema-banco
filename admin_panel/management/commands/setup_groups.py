from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from accounts.models import User, UserBankAccount
from transactions.models import Transaction


class Command(BaseCommand):
    help = 'Cria grupos de permissões para o sistema'

    def handle(self, *args, **kwargs):
        admin_group, _ = Group.objects.get_or_create(name='Administrador')
        supervisor_group, _ = Group.objects.get_or_create(name='Supervisor')
        operador_group, _ = Group.objects.get_or_create(name='Operador')

        user_ct = ContentType.objects.get_for_model(User)
        account_ct = ContentType.objects.get_for_model(UserBankAccount)
        transaction_ct = ContentType.objects.get_for_model(Transaction)

        admin_permissions = Permission.objects.filter(
            content_type__in=[user_ct, account_ct, transaction_ct]
        )
        admin_group.permissions.set(admin_permissions)

        supervisor_permissions = Permission.objects.filter(
            content_type__in=[user_ct, account_ct, transaction_ct],
            codename__in=[
                'view_user', 'change_user',
                'view_userbankaccount', 'change_userbankaccount',
                'view_transaction',
            ]
        )
        supervisor_group.permissions.set(supervisor_permissions)

        operador_permissions = Permission.objects.filter(
            content_type__in=[user_ct, account_ct, transaction_ct],
            codename__startswith='view_'
        )
        operador_group.permissions.set(operador_permissions)

        self.stdout.write(self.style.SUCCESS('Grupos criados com sucesso!'))
