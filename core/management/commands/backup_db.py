import os
import shutil
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Backup the SQLite database file with timestamp'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            help='Custom backup file path (default: db.sqlite3.backup.TIMESTAMP)',
        )

    def handle(self, *args, **options):
        db_path = settings.DATABASES['default']['NAME']
        
        if not os.path.exists(db_path):
            self.stdout.write(
                self.style.ERROR(f'Database file not found: {db_path}')
            )
            return

        if options['output']:
            backup_path = options['output']
        else:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = f'{db_path}.backup.{timestamp}'

        try:
            shutil.copy2(db_path, backup_path)
            
            original_size = os.path.getsize(db_path) / 1024
            backup_size = os.path.getsize(backup_path) / 1024
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Database backed up successfully!\n'
                    f'  Original: {db_path} ({original_size:.2f} KB)\n'
                    f'  Backup:   {backup_path} ({backup_size:.2f} KB)'
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to backup database: {str(e)}')
            )
