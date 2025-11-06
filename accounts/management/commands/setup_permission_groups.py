from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

from accounts.models import User, UserBankAccount, UserAddress, BankAccountType
from transactions.models import Transaction


class Command(BaseCommand):
    help = 'Create permission groups for bank staff'

    def handle(self, *args, **kwargs):
        account_managers, created = Group.objects.get_or_create(name='Account Managers')
        if created:
            self.stdout.write(self.style.SUCCESS('Created "Account Managers" group'))
        
        account_permissions = Permission.objects.filter(
            content_type__model__in=['user', 'userbankaccount', 'useraddress']
        )
        account_managers.permissions.set(account_permissions)
        self.stdout.write(self.style.SUCCESS(
            f'Added {account_permissions.count()} permissions to Account Managers'
        ))
        
        financial_officers, created = Group.objects.get_or_create(name='Financial Officers')
        if created:
            self.stdout.write(self.style.SUCCESS('Created "Financial Officers" group'))
        
        transaction_ct = ContentType.objects.get_for_model(Transaction)
        account_type_ct = ContentType.objects.get_for_model(BankAccountType)
        
        financial_permissions = Permission.objects.filter(
            content_type__in=[transaction_ct, account_type_ct]
        ) | Permission.objects.filter(
            content_type__model='userbankaccount',
            codename__startswith='view'
        )
        financial_officers.permissions.set(financial_permissions)
        self.stdout.write(self.style.SUCCESS(
            f'Added {financial_permissions.count()} permissions to Financial Officers'
        ))
        
        support_staff, created = Group.objects.get_or_create(name='Support Staff')
        if created:
            self.stdout.write(self.style.SUCCESS('Created "Support Staff" group'))
        
        support_permissions = Permission.objects.filter(
            content_type__model__in=['user', 'userbankaccount', 'useraddress', 'transaction'],
            codename__startswith='view'
        )
        support_staff.permissions.set(support_permissions)
        self.stdout.write(self.style.SUCCESS(
            f'Added {support_permissions.count()} permissions to Support Staff'
        ))
        
        self.stdout.write(self.style.SUCCESS('Successfully set up all permission groups'))
