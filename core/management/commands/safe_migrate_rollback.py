from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.apps import apps
from .backup_utils import DatabaseBackup
import sys

class Command(BaseCommand):
    help = '''
    Executa rollback de migrations de forma segura com validações de integridade.
    
    Exemplos:
        python manage.py safe_migrate_rollback accounts 0001
        python manage.py safe_migrate_rollback transactions zero --execute
    '''

    def add_arguments(self, parser):
        parser.add_argument(
            'app_label',
            type=str,
            help='Nome da app Django (ex: accounts, transactions)',
        )
        parser.add_argument(
            'migration_name',
            type=str,
            help='Nome ou número da migration alvo (ex: 0001, zero)',
        )
        parser.add_argument(
            '--execute',
            action='store_true',
            help='Executar o rollback (sem esta flag, apenas mostra o que seria feito)',
        )
        parser.add_argument(
            '--no-backup',
            action='store_true',
            help='Não criar backup antes do rollback (não recomendado)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forçar rollback mesmo com avisos (use com cautela)',
        )

    def handle(self, *args, **options):
        app_label = options['app_label']
        migration_name = options['migration_name']
        execute = options['execute']
        no_backup = options['no_backup']
        force = options['force']
        
        try:
            app_config = apps.get_app_config(app_label)
        except LookupError:
            raise CommandError(f"App '{app_label}' não encontrada")
        
        self.stdout.write(self.style.WARNING('\n' + '='*70))
        self.stdout.write(self.style.WARNING('SISTEMA DE ROLLBACK SEGURO DE MIGRATIONS'))
        self.stdout.write(self.style.WARNING('='*70 + '\n'))
        
        self.stdout.write("Verificando migrations aplicadas...")
        current_migrations = self._get_applied_migrations(app_label)
        
        if not current_migrations:
            self.stdout.write(self.style.ERROR(f"Nenhuma migration aplicada para '{app_label}'"))
            return
        
        self.stdout.write(f"Migrations aplicadas em '{app_label}':")
        for mig in current_migrations:
            self.stdout.write(f"  - {mig}")
        
        self.stdout.write("\nExecutando validações de segurança...")
        warnings = self._validate_rollback_safety(app_label, migration_name)
        
        if warnings:
            self.stdout.write(self.style.WARNING("\n⚠️  AVISOS ENCONTRADOS:"))
            for warning in warnings:
                self.stdout.write(self.style.WARNING(f"  - {warning}"))
            
            if not force:
                self.stdout.write(self.style.ERROR(
                    "\n❌ Rollback bloqueado por questões de segurança."
                ))
                self.stdout.write("Use --force para prosseguir (não recomendado)")
                sys.exit(1)
            else:
                self.stdout.write(self.style.WARNING(
                    "\n⚠️  Prosseguindo com rollback devido à flag --force"
                ))
        else:
            self.stdout.write(self.style.SUCCESS("✓ Validações de segurança passaram"))
        
        if not execute:
            self.stdout.write(self.style.WARNING(
                "\n🔍 MODO DRY-RUN: Nenhuma alteração será feita"
            ))
            self.stdout.write(f"\nO comando executaria:")
            self.stdout.write(f"  python manage.py migrate {app_label} {migration_name}")
            self.stdout.write("\nPara executar o rollback, adicione a flag --execute")
            return
        
        backup_path = None
        if not no_backup:
            self.stdout.write("\nCriando backup do banco de dados...")
            backup = DatabaseBackup()
            backup_path = backup.create_backup(f"before_rollback_{app_label}_{migration_name}")
            self.stdout.write(self.style.SUCCESS(f"✓ Backup criado: {backup_path}"))
        
        self.stdout.write(self.style.WARNING(
            f"\n🔄 Executando rollback de '{app_label}' para '{migration_name}'..."
        ))
        
        try:
            from django.core.management import call_command
            call_command('migrate', app_label, migration_name, verbosity=2)
            self.stdout.write(self.style.SUCCESS(
                f"\n✓ Rollback concluído com sucesso!"
            ))
            if backup_path:
                self.stdout.write(f"Backup disponível em: {backup_path}")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n❌ Erro durante rollback: {str(e)}"))
            if backup_path:
                self.stdout.write(f"Backup disponível para restauração em: {backup_path}")
            sys.exit(1)
    
    def _get_applied_migrations(self, app_label):
        """Retorna lista de migrations aplicadas para uma app"""
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT name FROM django_migrations WHERE app = %s ORDER BY id",
                [app_label]
            )
            return [row[0] for row in cursor.fetchall()]
    
    def _validate_rollback_safety(self, app_label, migration_name):
        """Valida se o rollback é seguro, retorna lista de avisos"""
        warnings = []
        
        dependencies = self._check_migration_dependencies(app_label)
        if dependencies:
            warnings.append(
                f"Outras apps dependem de migrations de '{app_label}': {', '.join(dependencies)}"
            )
        
        data_warnings = self._check_existing_data(app_label)
        warnings.extend(data_warnings)
        
        banking_warnings = self._validate_banking_constraints(app_label)
        warnings.extend(banking_warnings)
        
        return warnings
    
    def _check_migration_dependencies(self, app_label):
        """Verifica se outras apps dependem desta app"""
        dependent_apps = []
        
        if app_label == 'accounts':
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT COUNT(*) FROM django_migrations WHERE app = 'transactions'"
                )
                if cursor.fetchone()[0] > 0:
                    dependent_apps.append('transactions')
        
        return dependent_apps
    
    def _check_existing_data(self, app_label):
        """Verifica se existem dados nas tabelas da app"""
        warnings = []
        
        try:
            app_config = apps.get_app_config(app_label)
            for model in app_config.get_models():
                count = model.objects.count()
                if count > 0:
                    warnings.append(
                        f"Tabela '{model._meta.db_table}' contém {count} registros"
                    )
        except Exception as e:
            warnings.append(f"Erro ao verificar dados: {str(e)}")
        
        return warnings
    
    def _validate_banking_constraints(self, app_label):
        """Validações específicas para sistema bancário"""
        warnings = []
        
        if app_label == 'transactions':
            try:
                from transactions.models import Transaction
                transaction_count = Transaction.objects.count()
                if transaction_count > 0:
                    warnings.append(
                        f"⚠️  CRÍTICO: Sistema possui {transaction_count} transações bancárias. "
                        "Rollback pode causar perda de dados financeiros!"
                    )
                    
                    from django.db.models import Sum
                    from accounts.models import UserBankAccount
                    total_balance = UserBankAccount.objects.aggregate(
                        Sum('balance')
                    )['balance__sum'] or 0
                    
                    if total_balance > 0:
                        warnings.append(
                            f"⚠️  CRÍTICO: Saldo total do sistema: R$ {total_balance}. "
                            "Rollback afetará dados financeiros!"
                        )
            except Exception as e:
                warnings.append(f"Erro ao validar transações: {str(e)}")
        
        elif app_label == 'accounts':
            try:
                from accounts.models import UserBankAccount, User
                account_count = UserBankAccount.objects.count()
                user_count = User.objects.count()
                
                if account_count > 0:
                    warnings.append(
                        f"⚠️  CRÍTICO: Sistema possui {account_count} contas bancárias e "
                        f"{user_count} usuários. Rollback causará perda de dados!"
                    )
            except Exception as e:
                warnings.append(f"Erro ao validar contas: {str(e)}")
        
        return warnings
