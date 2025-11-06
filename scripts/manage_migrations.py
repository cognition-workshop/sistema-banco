#!/usr/bin/env python
"""
Script para gerenciar migrations com backup e rollback automático.
"""
import os
import sys
import subprocess
import shutil
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "banking_system.settings")

import django

django.setup()

from django.conf import settings
from django.core.management import call_command


class MigrationManager:
    """Gerenciador de migrations com backup e rollback."""

    def __init__(self):
        self.backup_dir = BASE_DIR / "backups"
        self.backup_dir.mkdir(exist_ok=True)

    def create_backup(self):
        """Cria backup do banco de dados antes de aplicar migrations."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if "sqlite3" in settings.DATABASES["default"]["ENGINE"]:
            db_path = settings.DATABASES["default"]["NAME"]
            backup_path = self.backup_dir / f"db_backup_{timestamp}.sqlite3"
            shutil.copy2(db_path, backup_path)
            print(f"✓ Backup criado: {backup_path}")
            return backup_path

        elif "postgresql" in settings.DATABASES["default"]["ENGINE"]:
            backup_path = self.backup_dir / f"db_backup_{timestamp}.sql"
            db_config = settings.DATABASES["default"]

            cmd = [
                "pg_dump",
                "-h",
                db_config["HOST"],
                "-p",
                db_config["PORT"],
                "-U",
                db_config["USER"],
                "-d",
                db_config["NAME"],
                "-f",
                str(backup_path),
            ]

            env = os.environ.copy()
            env["PGPASSWORD"] = db_config["PASSWORD"]

            result = subprocess.run(cmd, env=env, capture_output=True, text=True)

            if result.returncode == 0:
                print(f"✓ Backup criado: {backup_path}")
                return backup_path
            else:
                print(f"✗ Erro ao criar backup: {result.stderr}")
                return None

        else:
            print("✗ Tipo de banco de dados não suportado para backup")
            return None

    def validate_migrations(self):
        """Valida migrations antes de aplicar."""
        print("\n=== Validando migrations ===")
        try:
            call_command("makemigrations", "--dry-run", "--check")
            print("✓ Nenhuma migration pendente não criada")
            return True
        except SystemExit:
            print("✗ Existem migrations pendentes. Execute makemigrations primeiro.")
            return False

    def apply_migrations(self):
        """Aplica migrations com backup automático."""
        print("\n=== Iniciando processo de migration ===")

        if not self.validate_migrations():
            return False

        print("\n=== Criando backup ===")
        backup_path = self.create_backup()
        if not backup_path:
            print("✗ Falha ao criar backup. Abortando migration.")
            return False

        print("\n=== Aplicando migrations ===")
        try:
            call_command("migrate")
            print("✓ Migrations aplicadas com sucesso!")
            return True
        except Exception as e:
            print(f"✗ Erro ao aplicar migrations: {str(e)}")
            print("\n=== Iniciando rollback ===")
            self.rollback(backup_path)
            return False

    def rollback(self, backup_path):
        """Restaura backup em caso de erro."""
        print(f"Restaurando backup de {backup_path}...")

        if "sqlite3" in settings.DATABASES["default"]["ENGINE"]:
            db_path = settings.DATABASES["default"]["NAME"]
            shutil.copy2(backup_path, db_path)
            print("✓ Banco de dados restaurado com sucesso!")

        elif "postgresql" in settings.DATABASES["default"]["ENGINE"]:
            db_config = settings.DATABASES["default"]

            cmd_drop = [
                "psql",
                "-h",
                db_config["HOST"],
                "-p",
                db_config["PORT"],
                "-U",
                db_config["USER"],
                "-c",
                f"DROP DATABASE IF EXISTS {db_config['NAME']}",
            ]

            cmd_create = [
                "psql",
                "-h",
                db_config["HOST"],
                "-p",
                db_config["PORT"],
                "-U",
                db_config["USER"],
                "-c",
                f"CREATE DATABASE {db_config['NAME']}",
            ]

            cmd_restore = [
                "psql",
                "-h",
                db_config["HOST"],
                "-p",
                db_config["PORT"],
                "-U",
                db_config["USER"],
                "-d",
                db_config["NAME"],
                "-f",
                str(backup_path),
            ]

            env = os.environ.copy()
            env["PGPASSWORD"] = db_config["PASSWORD"]

            subprocess.run(cmd_drop, env=env)
            subprocess.run(cmd_create, env=env)
            result = subprocess.run(cmd_restore, env=env, capture_output=True, text=True)

            if result.returncode == 0:
                print("✓ Banco de dados restaurado com sucesso!")
            else:
                print(f"✗ Erro ao restaurar: {result.stderr}")

    def list_backups(self):
        """Lista todos os backups disponíveis."""
        backups = sorted(self.backup_dir.glob("db_backup_*"))

        if not backups:
            print("Nenhum backup encontrado.")
            return

        print("\n=== Backups disponíveis ===")
        for backup in backups:
            size_mb = backup.stat().st_size / (1024 * 1024)
            print(f"- {backup.name} ({size_mb:.2f} MB)")


def main():
    """Função principal."""
    manager = MigrationManager()

    if len(sys.argv) < 2:
        print(
            """
Uso: python manage_migrations.py [comando]

Comandos disponíveis:
  apply      - Aplica migrations com backup automático
  backup     - Cria backup do banco de dados
  validate   - Valida migrations pendentes
  list       - Lista backups disponíveis
        """
        )
        return

    command = sys.argv[1]

    if command == "apply":
        manager.apply_migrations()
    elif command == "backup":
        manager.create_backup()
    elif command == "validate":
        manager.validate_migrations()
    elif command == "list":
        manager.list_backups()
    else:
        print(f"Comando desconhecido: {command}")


if __name__ == "__main__":
    main()
