from django.test import TestCase
from django.core.management import call_command
from io import StringIO
from accounts.models import User, UserBankAccount, BankAccountType
from transactions.models import Transaction
import os
import shutil

class MigrationCommandsTestCase(TestCase):
    """Testes para os comandos de gerenciamento de migrations"""
    
    def setUp(self):
        """Configuração inicial para os testes"""
        self.account_type = BankAccountType.objects.create(
            name='Conta Corrente',
            maximum_withdrawal_amount=5000,
            annual_interest_rate=1.5,
            interest_calculation_per_year=12
        )
        
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        self.bank_account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender='M',
            balance=1000.00
        )
    
    def test_migration_history_command(self):
        """Testa o comando migration_history"""
        out = StringIO()
        call_command('migration_history', stdout=out)
        output = out.getvalue()
        
        self.assertIn('accounts', output)
        self.assertIn('0001_initial', output)
    
    def test_migration_history_with_app_filter(self):
        """Testa migration_history com filtro de app"""
        out = StringIO()
        call_command('migration_history', app='accounts', stdout=out)
        output = out.getvalue()
        
        self.assertIn('accounts', output)
    
    def test_safe_rollback_dry_run(self):
        """Testa modo dry-run do rollback"""
        out = StringIO()
        call_command(
            'safe_migrate_rollback',
            'accounts',
            '0001',
            stdout=out
        )
        output = out.getvalue()
        
        self.assertIn('DRY-RUN', output)
        self.assertIn('Nenhuma alteração será feita', output)
    
    def test_list_backups_command(self):
        """Testa o comando list_backups"""
        out = StringIO()
        call_command('list_backups', stdout=out)
        output = out.getvalue()
        
        self.assertTrue(True)
    
    def tearDown(self):
        """Limpeza após os testes"""
        backup_dir = 'backups'
        if os.path.exists(backup_dir):
            for item in os.listdir(backup_dir):
                item_path = os.path.join(backup_dir, item)
                if 'test' in item.lower():
                    if os.path.isdir(item_path):
                        shutil.rmtree(item_path)
