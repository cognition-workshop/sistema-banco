#!/usr/bin/env python
import os
import sys
import shutil
from datetime import datetime
import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "banking_system.settings")
django.setup()

from django.conf import settings  # noqa: E402
from django.core.management import call_command  # noqa: E402

BACKUP_DIR = settings.BASE_DIR / "backups"


def create_backup():
    BACKUP_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = BACKUP_DIR / f"db_backup_{timestamp}.sqlite3"

    db_path = settings.DATABASES["default"]["NAME"]

    try:
        shutil.copy2(db_path, backup_file)
        print(f"✓ Backup created: {backup_file}")
        return backup_file
    except Exception as e:
        print(f"✗ Backup failed: {e}")
        return None


def validate_migrations():
    try:
        call_command("makemigrations", "--check", "--dry-run")
        print("✓ No pending model changes")
        return True
    except SystemExit:
        print("✗ Warning: Pending model changes detected")
        return False


def apply_migrations():
    print("=== Migration Process ===")

    if not validate_migrations():
        response = input("Continue anyway? (yes/no): ")
        if response.lower() != "yes":
            print("Migration cancelled")
            return False

    backup_file = create_backup()
    if not backup_file:
        print("Migration cancelled due to backup failure")
        return False

    try:
        print("\nApplying migrations...")
        call_command("migrate")
        print("✓ Migrations applied successfully")
        return True
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        print(f"Backup available at: {backup_file}")
        return False


def rollback_migration(app_name, migration_name):
    backup_file = create_backup()
    if not backup_file:
        print("Rollback cancelled due to backup failure")
        return False

    try:
        print(f"Rolling back {app_name} to {migration_name}...")
        call_command("migrate", app_name, migration_name)
        print("✓ Rollback successful")
        return True
    except Exception as e:
        print(f"✗ Rollback failed: {e}")
        print(f"Backup available at: {backup_file}")
        return False


def list_migrations():
    call_command("showmigrations")


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python scripts/migration_manager.py apply")
        print(
            "  python scripts/migration_manager.py rollback <app_name> <migration_name>"
        )
        print("  python scripts/migration_manager.py list")
        print("  python scripts/migration_manager.py validate")
        sys.exit(1)

    command = sys.argv[1]

    if command == "apply":
        apply_migrations()
    elif command == "rollback":
        if len(sys.argv) < 4:
            print(
                "Usage: python scripts/migration_manager.py rollback <app_name> <migration_name>"
            )
            sys.exit(1)
        rollback_migration(sys.argv[2], sys.argv[3])
    elif command == "list":
        list_migrations()
    elif command == "validate":
        validate_migrations()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
