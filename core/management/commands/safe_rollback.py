import os
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings


class Command(BaseCommand):
    help = 'Safely rollback migrations in correct order with automatic backup'

    def add_arguments(self, parser):
        parser.add_argument(
            '--to-zero',
            action='store_true',
            help='Roll back all migrations to zero',
        )
        parser.add_argument(
            '--transactions-migration',
            type=str,
            default='zero',
            help='Migration to roll back transactions app to (default: zero)',
        )
        parser.add_argument(
            '--accounts-migration',
            type=str,
            default='zero',
            help='Migration to roll back accounts app to (default: zero)',
        )
        parser.add_argument(
            '--no-backup',
            action='store_true',
            help='Skip automatic database backup (not recommended)',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('=' * 70))
        self.stdout.write(self.style.WARNING('SAFE MIGRATION ROLLBACK'))
        self.stdout.write(self.style.WARNING('=' * 70))
        
        if not options['no_backup']:
            self.stdout.write('\n[Step 1/4] Backing up database...')
            try:
                call_command('backup_db')
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Backup failed: {str(e)}')
                )
                self.stdout.write(
                    self.style.ERROR('Aborting rollback for safety.')
                )
                return
        else:
            self.stdout.write(
                self.style.WARNING(
                    '\n[Step 1/4] ⚠️  Skipping backup (--no-backup flag used)'
                )
            )

        self.stdout.write('\n[Step 2/4] Current migration status:')
        call_command('showmigrations', 'accounts', 'transactions')

        transactions_target = 'zero' if options['to_zero'] else options['transactions_migration']
        accounts_target = 'zero' if options['to_zero'] else options['accounts_migration']

        self.stdout.write(
            self.style.WARNING(
                f'\n[Step 3/4] Rolling back transactions app to: {transactions_target}'
            )
        )
        try:
            call_command('migrate', 'transactions', transactions_target)
            self.stdout.write(
                self.style.SUCCESS('✓ Transactions app rolled back successfully')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f'Failed to roll back transactions app: {str(e)}'
                )
            )
            self.stdout.write(
                self.style.ERROR(
                    'Stopping rollback. You may need to restore from backup.'
                )
            )
            return

        self.stdout.write(
            self.style.WARNING(
                f'\n[Step 4/4] Rolling back accounts app to: {accounts_target}'
            )
        )
        try:
            call_command('migrate', 'accounts', accounts_target)
            self.stdout.write(
                self.style.SUCCESS('✓ Accounts app rolled back successfully')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to roll back accounts app: {str(e)}')
            )
            self.stdout.write(
                self.style.ERROR(
                    'Transactions app was rolled back but accounts failed. '
                    'You may need to restore from backup.'
                )
            )
            return

        self.stdout.write('\n' + '=' * 70)
        self.stdout.write(self.style.SUCCESS('✓ ROLLBACK COMPLETED SUCCESSFULLY'))
        self.stdout.write('=' * 70)
        self.stdout.write('\nFinal migration status:')
        call_command('showmigrations', 'accounts', 'transactions')
        
        self.stdout.write(
            self.style.SUCCESS(
                '\n✓ All migrations rolled back in correct order!'
            )
        )
