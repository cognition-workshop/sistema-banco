#!/usr/bin/env python
"""
Migration script to export data from SQLite and import to PostgreSQL.
This script migrates all data while preserving foreign key relationships.

Usage:
    python migrate_sqlite_to_postgres.py
"""
import os
import sys
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'banking_system.settings')
django.setup()

from django.db import connection
from django.contrib.auth import get_user_model
from accounts.models import BankAccountType, UserBankAccount, UserAddress
from transactions.models import Transaction

import sqlite3
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


def create_postgres_database():
    """Create PostgreSQL database if it doesn't exist."""
    print("Checking PostgreSQL database...")
    
    try:
        conn = psycopg2.connect(
            dbname='postgres',
            user='postgres',
            password='postgres',
            host='localhost',
            port='5432'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        cursor.execute("SELECT 1 FROM pg_database WHERE datname='banking_system_db'")
        exists = cursor.fetchone()
        
        if not exists:
            print("Creating database 'banking_system_db'...")
            cursor.execute("CREATE DATABASE banking_system_db")
            print("Database created successfully!")
        else:
            print("Database 'banking_system_db' already exists.")
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error creating database: {e}")
        sys.exit(1)


def export_from_sqlite():
    """Export all data from SQLite database."""
    print("\nExporting data from SQLite...")
    
    sqlite_db_path = os.path.join(settings.BASE_DIR, 'db.sqlite3')
    
    if not os.path.exists(sqlite_db_path):
        print(f"SQLite database not found at {sqlite_db_path}")
        print("Skipping data export. You can start with a fresh PostgreSQL database.")
        return None
    
    conn = sqlite3.connect(sqlite_db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    data = {
        'bank_account_types': [],
        'users': [],
        'user_bank_accounts': [],
        'user_addresses': [],
        'transactions': [],
    }
    
    try:
        cursor.execute("SELECT * FROM accounts_bankaccounttype")
        data['bank_account_types'] = [dict(row) for row in cursor.fetchall()]
        print(f"  Exported {len(data['bank_account_types'])} bank account types")
        
        cursor.execute("SELECT * FROM accounts_user")
        data['users'] = [dict(row) for row in cursor.fetchall()]
        print(f"  Exported {len(data['users'])} users")
        
        cursor.execute("SELECT * FROM accounts_userbankaccount")
        data['user_bank_accounts'] = [dict(row) for row in cursor.fetchall()]
        print(f"  Exported {len(data['user_bank_accounts'])} user bank accounts")
        
        cursor.execute("SELECT * FROM accounts_useraddress")
        data['user_addresses'] = [dict(row) for row in cursor.fetchall()]
        print(f"  Exported {len(data['user_addresses'])} user addresses")
        
        cursor.execute("SELECT * FROM transactions_transaction")
        data['transactions'] = [dict(row) for row in cursor.fetchall()]
        print(f"  Exported {len(data['transactions'])} transactions")
        
    except sqlite3.Error as e:
        print(f"Error exporting from SQLite: {e}")
        conn.close()
        return None
    
    conn.close()
    return data


def import_to_postgres(data):
    """Import data to PostgreSQL using Django ORM."""
    if data is None:
        print("\nNo data to import. Database will be empty.")
        return
    
    print("\nImporting data to PostgreSQL...")
    
    User = get_user_model()
    
    try:
        print("  Importing bank account types...")
        for row in data['bank_account_types']:
            BankAccountType.objects.get_or_create(
                id=row['id'],
                defaults={
                    'name': row['name'],
                    'maximum_withdrawal_amount': row['maximum_withdrawal_amount'],
                    'annual_interest_rate': row['annual_interest_rate'],
                    'interest_calculation_per_year': row['interest_calculation_per_year'],
                }
            )
        
        print("  Importing users...")
        for row in data['users']:
            User.objects.get_or_create(
                id=row['id'],
                defaults={
                    'email': row['email'],
                    'password': row['password'],
                    'first_name': row['first_name'],
                    'last_name': row['last_name'],
                    'is_superuser': row['is_superuser'],
                    'is_staff': row['is_staff'],
                    'is_active': row['is_active'],
                    'date_joined': row['date_joined'],
                    'last_login': row['last_login'],
                }
            )
        
        print("  Importing user bank accounts...")
        for row in data['user_bank_accounts']:
            UserBankAccount.objects.get_or_create(
                id=row['id'],
                defaults={
                    'user_id': row['user_id'],
                    'account_type_id': row['account_type_id'],
                    'account_no': row['account_no'],
                    'gender': row['gender'],
                    'birth_date': row['birth_date'],
                    'balance': row['balance'],
                    'interest_start_date': row['interest_start_date'],
                    'initial_deposit_date': row['initial_deposit_date'],
                }
            )
        
        print("  Importing user addresses...")
        for row in data['user_addresses']:
            UserAddress.objects.get_or_create(
                id=row['id'],
                defaults={
                    'user_id': row['user_id'],
                    'street_address': row['street_address'],
                    'city': row['city'],
                    'postal_code': row['postal_code'],
                    'country': row['country'],
                }
            )
        
        print("  Importing transactions...")
        for row in data['transactions']:
            Transaction.objects.get_or_create(
                id=row['id'],
                defaults={
                    'account_id': row['account_id'],
                    'amount': row['amount'],
                    'balance_after_transaction': row['balance_after_transaction'],
                    'transaction_type': row['transaction_type'],
                    'timestamp': row['timestamp'],
                }
            )
        
        print("\nData import completed successfully!")
        
    except Exception as e:
        print(f"Error importing to PostgreSQL: {e}")
        raise


def verify_integrity():
    """Verify foreign key integrity after migration."""
    print("\nVerifying foreign key integrity...")
    
    User = get_user_model()
    
    try:
        bank_account_types_count = BankAccountType.objects.count()
        users_count = User.objects.count()
        user_bank_accounts_count = UserBankAccount.objects.count()
        user_addresses_count = UserAddress.objects.count()
        transactions_count = Transaction.objects.count()
        
        print(f"  Bank Account Types: {bank_account_types_count}")
        print(f"  Users: {users_count}")
        print(f"  User Bank Accounts: {user_bank_accounts_count}")
        print(f"  User Addresses: {user_addresses_count}")
        print(f"  Transactions: {transactions_count}")
        
        print("\n  Checking foreign key relationships...")
        for account in UserBankAccount.objects.all():
            assert account.user is not None, f"Account {account.id} has no user"
            assert account.account_type is not None, f"Account {account.id} has no account type"
        
        for address in UserAddress.objects.all():
            assert address.user is not None, f"Address {address.id} has no user"
        
        for transaction in Transaction.objects.all():
            assert transaction.account is not None, f"Transaction {transaction.id} has no account"
        
        print("  All foreign key relationships are valid!")
        
    except AssertionError as e:
        print(f"  Integrity check failed: {e}")
        raise
    except Exception as e:
        print(f"  Error during integrity check: {e}")
        raise


def main():
    """Main migration process."""
    print("=" * 60)
    print("SQLite to PostgreSQL Migration Script")
    print("=" * 60)
    
    create_postgres_database()
    
    data = export_from_sqlite()
    
    print("\nApplying Django migrations to PostgreSQL...")
    from django.core.management import call_command
    call_command('migrate', '--noinput')
    
    import_to_postgres(data)
    
    verify_integrity()
    
    print("\n" + "=" * 60)
    print("Migration completed successfully!")
    print("=" * 60)
    print("\nYou can now use PostgreSQL with your Django application.")
    print("Run 'python manage.py runserver' to start the development server.")


if __name__ == '__main__':
    main()
