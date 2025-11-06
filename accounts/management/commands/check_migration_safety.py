from django.core.management.base import BaseCommand
from django.db import connection
from accounts.models import User, UserBankAccount, UserAddress, BankAccountType
from transactions.models import Transaction


class Command(BaseCommand):
    help = 'Verifica o impacto de reverter migrations e alerta sobre perda de dados'

    def add_arguments(self, parser):
        parser.add_argument(
            'app_name',
            type=str,
            help='Nome do app para verificar (accounts ou transactions)'
        )

    def handle(self, *args, **options):
        app_name = options['app_name']
        
        self.stdout.write(self.style.WARNING('\n' + '='*70))
        self.stdout.write(self.style.WARNING('VERIFICAÇÃO DE SEGURANÇA DE ROLLBACK DE MIGRATIONS'))
        self.stdout.write(self.style.WARNING('='*70 + '\n'))

        if app_name == 'transactions':
            self.check_transactions_rollback()
        elif app_name == 'accounts':
            self.check_accounts_rollback()
        else:
            self.stdout.write(
                self.style.ERROR(f'App "{app_name}" não reconhecido. Use "accounts" ou "transactions".')
            )
            return

        self.stdout.write('\n' + '='*70 + '\n')

    def check_transactions_rollback(self):
        """Verifica impacto de reverter migrations do app transactions"""
        transaction_count = Transaction.objects.count()
        
        self.stdout.write(
            self.style.WARNING(f'📊 App: transactions')
        )
        self.stdout.write(
            f'   Registros na tabela Transaction: {transaction_count}'
        )
        
        if transaction_count > 0:
            self.stdout.write(
                self.style.ERROR(
                    f'\n⚠️  AVISO: Reverter transactions para zero deletará {transaction_count} transações!'
                )
            )
            self.stdout.write(
                '   • A tabela Transaction será completamente removida'
            )
            self.stdout.write(
                '   • Todos os registros de transações serão perdidos'
            )
            self.stdout.write(
                '\n💡 Recomendação: Execute "python backup_database.py" antes de continuar'
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('\n✓ Nenhum dado será perdido (tabela vazia)')
            )

    def check_accounts_rollback(self):
        """Verifica impacto de reverter migrations do app accounts"""
        user_count = User.objects.count()
        account_count = UserBankAccount.objects.count()
        address_count = UserAddress.objects.count()
        account_type_count = BankAccountType.objects.count()
        transaction_count = Transaction.objects.count()
        
        self.stdout.write(self.style.WARNING(f'📊 App: accounts'))
        self.stdout.write(f'   Registros na tabela User: {user_count}')
        self.stdout.write(f'   Registros na tabela UserBankAccount: {account_count}')
        self.stdout.write(f'   Registros na tabela UserAddress: {address_count}')
        self.stdout.write(f'   Registros na tabela BankAccountType: {account_type_count}')
        
        total_records = user_count + account_count + address_count + account_type_count
        
        if total_records > 0:
            self.stdout.write(
                self.style.ERROR(
                    f'\n⚠️  AVISO CRÍTICO: Reverter accounts para zero causará CASCADE DELETE!'
                )
            )
            self.stdout.write(
                '\n📋 Dados que serão perdidos:'
            )
            self.stdout.write(f'   • {user_count} usuários')
            self.stdout.write(f'   • {account_count} contas bancárias')
            self.stdout.write(f'   • {address_count} endereços')
            self.stdout.write(f'   • {account_type_count} tipos de conta')
            self.stdout.write(f'   • {transaction_count} transações (deletadas por CASCADE)')
            
            self.stdout.write(
                self.style.ERROR(
                    f'\n🚨 TOTAL: {total_records + transaction_count} registros serão perdidos!'
                )
            )
            
            self.stdout.write(
                '\n⚠️  Relações CASCADE:'
            )
            self.stdout.write('   • Transaction.account → UserBankAccount (CASCADE)')
            self.stdout.write('   • UserBankAccount.user → User (CASCADE)')
            self.stdout.write('   • UserAddress.user → User (CASCADE)')
            self.stdout.write('   • UserBankAccount.account_type → BankAccountType (CASCADE)')
            
            self.stdout.write(
                '\n💡 Recomendação: Execute "python backup_database.py" antes de continuar'
            )
            
            self.stdout.write(
                '\n📖 Ordem de rollback recomendada:'
            )
            self.stdout.write('   1. python manage.py migrate transactions zero')
            self.stdout.write('   2. python manage.py migrate accounts zero')
        else:
            self.stdout.write(
                self.style.SUCCESS('\n✓ Nenhum dado será perdido (tabelas vazias)')
            )
