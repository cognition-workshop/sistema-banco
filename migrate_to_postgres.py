"""
Script to migrate data from SQLite to PostgreSQL.
Run this after setting up PostgreSQL database.

Usage:
    1. Set DATABASE_URL environment variable to PostgreSQL connection string
    2. Run: python migrate_to_postgres.py
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'banking_system.settings')
django.setup()

from django.core.management import call_command
from django.db import connection
import sqlite3


def migrate_data():
    """Migrate data from SQLite to PostgreSQL"""
    sqlite_db = 'db.sqlite3'
    
    if not os.path.exists(sqlite_db):
        print(f"SQLite database {sqlite_db} not found!")
        return
    
    print("Step 1: Running migrations on PostgreSQL...")
    call_command('migrate', '--run-syncdb')
    
    print("\nStep 2: Dumping data from SQLite...")
    call_command('dumpdata', 
                 '--natural-foreign', 
                 '--natural-primary',
                 '--exclude=contenttypes',
                 '--exclude=auth.permission',
                 '--indent=2',
                 output='data_dump.json')
    
    print("\nStep 3: Loading data into PostgreSQL...")
    call_command('loaddata', 'data_dump.json')
    
    print("\n✅ Migration completed successfully!")
    print("You can now delete db.sqlite3 and data_dump.json")


if __name__ == '__main__':
    migrate_data()
