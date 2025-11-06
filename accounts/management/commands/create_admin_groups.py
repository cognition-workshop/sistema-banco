from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from accounts.models import User, UserBankAccount, UserAddress
from transactions.models import Transaction, FraudAlert


class Command(BaseCommand):
    help = 'Cria grupos de permissão para o painel administrativo'

    def handle(self, *args, **kwargs):
        admin_total, created = Group.objects.get_or_create(name='admin_total')
        if created:
            all_permissions = Permission.objects.all()
            admin_total.permissions.set(all_permissions)
            self.stdout.write(self.style.SUCCESS('Grupo "admin_total" criado com todas as permissões'))
        
        admin_transacoes, created = Group.objects.get_or_create(name='admin_transacoes')
        if created:
            transaction_ct = ContentType.objects.get_for_model(Transaction)
            fraud_ct = ContentType.objects.get_for_model(FraudAlert)
            
            permissions = Permission.objects.filter(
                content_type__in=[transaction_ct, fraud_ct]
            )
            admin_transacoes.permissions.set(permissions)
            self.stdout.write(self.style.SUCCESS('Grupo "admin_transacoes" criado'))
        
        admin_usuarios, created = Group.objects.get_or_create(name='admin_usuarios')
        if created:
            user_ct = ContentType.objects.get_for_model(User)
            account_ct = ContentType.objects.get_for_model(UserBankAccount)
            address_ct = ContentType.objects.get_for_model(UserAddress)
            
            permissions = Permission.objects.filter(
                content_type__in=[user_ct, account_ct, address_ct]
            )
            admin_usuarios.permissions.set(permissions)
            self.stdout.write(self.style.SUCCESS('Grupo "admin_usuarios" criado'))
        
        self.stdout.write(self.style.SUCCESS('Todos os grupos foram configurados com sucesso!'))
