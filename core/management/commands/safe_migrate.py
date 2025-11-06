from django.core.management.base import BaseCommand
from django.core.management import call_command
import shutil
from pathlib import Path
from datetime import datetime


class Command(BaseCommand):
    help = "Executa migrations com backup automático"

    def handle(self, *args, **options):
        self.stdout.write("=== Migração Segura ===")

        db_path = Path("db.sqlite3")
        backup_path = None

        if db_path.exists():
            backup_dir = Path("backups")
            backup_dir.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = backup_dir / f"db_backup_{timestamp}.sqlite3"

            self.stdout.write("Criando backup...")
            shutil.copy(db_path, backup_path)
            self.stdout.write(self.style.SUCCESS(f"✓ Backup criado: {backup_path}"))

        try:
            self.stdout.write("Executando migrations...")
            call_command("migrate", verbosity=1)
            self.stdout.write(
                self.style.SUCCESS("✓ Migrations executadas com sucesso!")
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Erro: {str(e)}"))

            if db_path.exists() and backup_path and backup_path.exists():
                self.stdout.write("Restaurando backup...")
                shutil.copy(backup_path, db_path)
                self.stdout.write(self.style.SUCCESS("✓ Backup restaurado"))

            raise
