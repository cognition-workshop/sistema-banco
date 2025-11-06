from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

from accounts.models import User, UserBankAccount, BankAccountType, UserAddress
from transactions.models import Transaction


class Command(BaseCommand):
    help = 'Create admin permission groups'

    def handle(self, *args, **options):
        account_managers, created = Group.objects.get_or_create(name='Account Managers')
        if created:
            user_ct = ContentType.objects.get_for_model(User)
            account_ct = ContentType.objects.get_for_model(UserBankAccount)
            address_ct = ContentType.objects.get_for_model(UserAddress)
            
            permissions = Permission.objects.filter(
                content_type__in=[user_ct, account_ct, address_ct]
            ).exclude(codename__startswith='delete')
            
            account_managers.permissions.set(permissions)
            self.stdout.write(self.style.SUCCESS('Created Account Managers group'))
        
        financial_officers, created = Group.objects.get_or_create(name='Financial Officers')
        if created:
            transaction_ct = ContentType.objects.get_for_model(Transaction)
            account_type_ct = ContentType.objects.get_for_model(BankAccountType)
            
            permissions = Permission.objects.filter(
                content_type__in=[transaction_ct, account_type_ct],
                codename__startswith='view'
            )
            
            financial_officers.permissions.set(permissions)
            self.stdout.write(self.style.SUCCESS('Created Financial Officers group'))
        
        support_staff, created = Group.objects.get_or_create(name='Support Staff')
        if created:
            all_cts = [
                ContentType.objects.get_for_model(model) 
                for model in [User, UserBankAccount, UserAddress, Transaction, BankAccountType]
            ]
            
            permissions = Permission.objects.filter(
                content_type__in=all_cts,
                codename__startswith='view'
            )
            
            support_staff.permissions.set(permissions)
            self.stdout.write(self.style.SUCCESS('Created Support Staff group'))
        
        self.stdout.write(self.style.SUCCESS('All admin groups created successfully!'))
