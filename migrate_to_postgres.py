#!/usr/bin/env python
"""
Script to migrate data from SQLite to PostgreSQL
Usage:
    1. Backup SQLite data: python migrate_to_postgres.py backup
    2. Load into PostgreSQL: python migrate_to_postgres.py load
"""
import os
import sys
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "banking_system.settings")
django.setup()

from django.core.management import call_command  # noqa: E402


def backup_data():
    """Backup data from current database to JSON file"""
    print("Backing up data from SQLite...")
    with open("backup_data.json", "w") as f:
        call_command(
            "dumpdata",
            "--natural-foreign",
            "--natural-primary",
            "--indent=2",
            "--exclude=contenttypes",
            "--exclude=auth.Permission",
            stdout=f,
        )
    print("✓ Data backed up to backup_data.json")


def load_data():
    """Load data into current database from JSON file"""
    print("Loading data into PostgreSQL...")
    if not os.path.exists("backup_data.json"):
        print("Error: backup_data.json not found. Run backup first.")
        sys.exit(1)

    call_command("loaddata", "backup_data.json")
    print("✓ Data loaded successfully")


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ["backup", "load"]:
        print(__doc__)
        sys.exit(1)

    if sys.argv[1] == "backup":
        backup_data()
    elif sys.argv[1] == "load":
        load_data()
