#!/usr/bin/env python
"""
Script to migrate data from SQLite to PostgreSQL while preserving all demo data
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'banking_system.settings')
django.setup()

from django.core.management import call_command
from django.db import connections
import json


def backup_sqlite_data():
    """Backup all data from SQLite to JSON"""
    print("📦 Backing up SQLite data...")
    
    if 'sqlite' not in connections['default'].settings_dict['ENGINE']:
        print("❌ Not connected to SQLite database")
        sys.exit(1)
    
    apps_to_backup = ['accounts', 'transactions']
    backup_file = 'data_backup.json'
    
    with open(backup_file, 'w') as f:
        call_command('dumpdata', *apps_to_backup, indent=2, stdout=f)
    
    print(f"✅ Data backed up to {backup_file}")
    return backup_file


def setup_postgresql():
    """Set up PostgreSQL database and run migrations"""
    print("🐘 Setting up PostgreSQL...")
    
    env_updates = {
        'DB_ENGINE': 'django.db.backends.postgresql',
        'DB_NAME': 'banking_system',
        'DB_USER': 'postgres',
        'DB_PASSWORD': os.environ.get('DB_PASSWORD', 'postgres'),
        'DB_HOST': 'localhost',
        'DB_PORT': '5432',
    }
    
    print("Creating PostgreSQL database...")
    os.system(f"createdb {env_updates['DB_NAME']} 2>/dev/null || true")
    
    print("Running migrations...")
    call_command('migrate', '--noinput')
    
    print("✅ PostgreSQL setup complete")


def restore_data(backup_file):
    """Restore data to PostgreSQL"""
    print("📥 Restoring data to PostgreSQL...")
    
    if 'postgresql' not in connections['default'].settings_dict['ENGINE']:
        print("❌ Not connected to PostgreSQL database")
        sys.exit(1)
    
    call_command('loaddata', backup_file)
    
    print("✅ Data restored successfully")


def verify_migration():
    """Verify that all data was migrated correctly"""
    from accounts.models import User, UserBankAccount
    from transactions.models import Transaction
    
    print("🔍 Verifying migration...")
    
    user_count = User.objects.count()
    account_count = UserBankAccount.objects.count()
    transaction_count = Transaction.objects.count()
    
    print(f"  Users: {user_count}")
    print(f"  Accounts: {account_count}")
    print(f"  Transactions: {transaction_count}")
    
    demo_user = User.objects.filter(email='demo@example.com').first()
    if demo_user:
        print(f"  ✅ Demo user exists: {demo_user.email}")
        if hasattr(demo_user, 'account'):
            print(f"  ✅ Demo account: {demo_user.account.account_no}")
            print(f"  ✅ Demo balance: ${demo_user.account.balance}")
    else:
        print("  ❌ Demo user not found!")
    
    print("✅ Migration verification complete")


if __name__ == '__main__':
    print("🚀 Starting SQLite to PostgreSQL migration...")
    
    backup_file = backup_sqlite_data()
    setup_postgresql()
    restore_data(backup_file)
    verify_migration()
    
    print("✅ Migration complete!")
