#!/usr/bin/env python
"""
Migrate data from SQLite to PostgreSQL

Usage:
1. First run this script with SQLite configured in settings.py:
   python migrate_sqlite_to_postgres.py

2. Then switch to PostgreSQL in settings.py and run:
   python manage.py migrate
   python manage.py loaddata data_backup.json
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'banking_system.settings')
django.setup()

from django.core import serializers
from accounts.models import User, BankAccountType, UserBankAccount, UserAddress
from transactions.models import Transaction

def export_data():
    print("Exporting data from current database...")
    
    models_to_export = [
        ('BankAccountType', BankAccountType),
        ('User', User),
        ('UserBankAccount', UserBankAccount),
        ('UserAddress', UserAddress),
        ('Transaction', Transaction),
    ]
    
    all_data = []
    
    for model_name, model_class in models_to_export:
        objects = model_class.objects.all()
        count = objects.count()
        print(f"  Exporting {count} {model_name} records...")
        
        if count > 0:
            serialized = serializers.serialize('json', objects, indent=2)
            all_data.append(serialized[1:-1])
    
    with open('data_backup.json', 'w') as f:
        f.write('[\n' + ',\n'.join(all_data) + '\n]')
    
    print("\nData exported successfully to data_backup.json")
    print("\nNext steps:")
    print("1. Update banking_system/settings.py to use PostgreSQL configuration")
    print("2. Run: python manage.py migrate")
    print("3. Run: python manage.py loaddata data_backup.json")
    print("\nNote: Make sure PostgreSQL is running and the database is created")
    print("      You can use ./setup_postgres.sh to create the database")

if __name__ == '__main__':
    try:
        export_data()
    except Exception as e:
        print(f"\nError during export: {e}")
        sys.exit(1)
