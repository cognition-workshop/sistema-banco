from django.core.management.base import BaseCommand
from .backup_utils import DatabaseBackup
from datetime import datetime

class Command(BaseCommand):
    help = 'Lista todos os backups disponíveis do banco de dados'

    def handle(self, *args, **options):
        backup = DatabaseBackup()
        backups = backup.list_backups()
        
        if not backups:
            self.stdout.write("Nenhum backup encontrado")
            return
        
        self.stdout.write(self.style.SUCCESS('\n=== Backups Disponíveis ===\n'))
        
        for b in backups:
            self.stdout.write(self.style.WARNING(f"\nBackup: {b['name']}"))
            self.stdout.write(f"  Data: {b['timestamp']}")
            self.stdout.write(f"  Descrição: {b.get('description', 'N/A')}")
            self.stdout.write(f"  Engine: {b.get('database_engine', 'N/A')}")
            self.stdout.write(f"  Path: {b['path']}")
        
        self.stdout.write(f"\n\nTotal: {len(backups)} backups")
