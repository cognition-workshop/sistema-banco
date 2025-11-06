# Django Migration Rollback Guide

## Overview

This guide explains how to safely roll back database migrations in the Banking System project. Django migrations are **reversible by default**, meaning you can undo migrations to revert your database schema to a previous state.

## Important Notes

⚠️ **CRITICAL WARNINGS:**
- Always backup your database before performing any rollback operations
- Always test rollbacks in development before applying to production
- Follow the correct rollback order due to foreign key dependencies
- Some migrations may not be reversible if they involve data loss operations

## Database Configuration

This project uses SQLite with the database file located at: `db.sqlite3`

## Migration Dependencies

The project has two main apps with migrations:
- `accounts` app: Creates User, BankAccountType, UserBankAccount, and UserAddress models
- `transactions` app: Creates Transaction model with foreign key to UserBankAccount

**Dependency Chain:**
```
transactions.0001_initial → accounts.0001_initial → auth.0012_alter_user_first_name_max_length
```

## Rollback Order

Due to CASCADE foreign key relationships, you **MUST** roll back in this order:

1. **First**: Roll back `transactions` app
2. **Second**: Roll back `accounts` app

Rolling back in the wrong order will cause foreign key constraint errors.

## Pre-Rollback: Backup Your Database

### Manual Backup
Before any rollback operation, create a backup:

```bash
cp db.sqlite3 db.sqlite3.backup.$(date +%Y%m%d_%H%M%S)
```

### Automated Backup (Using Helper Command)
We provide a management command that automatically backs up the database:

```bash
python manage.py backup_db
```

This creates a timestamped backup file like `db.sqlite3.backup.20231106_143022`.

## Viewing Migration Status

### Show All Migrations
To view the current migration status for all apps:

```bash
python manage.py showmigrations
```

Example output:
```
accounts
 [X] 0001_initial
transactions
 [X] 0001_initial
```

### Show Specific App Migrations
To view migrations for a specific app:

```bash
python manage.py showmigrations accounts
python manage.py showmigrations transactions
```

## Rolling Back Migrations

### Syntax
```bash
python manage.py migrate <app_name> <migration_name>
```

### Roll Back to Zero (Remove All Migrations)

To completely remove all migrations from an app:

```bash
python manage.py migrate transactions zero

python manage.py migrate accounts zero
```

### Roll Back to Specific Migration

To roll back to a specific migration (useful if you have multiple migrations):

```bash
python manage.py migrate transactions 0001_initial

python manage.py migrate accounts 0001_initial
```

### Roll Back One Migration

To undo just the last migration:

```bash
python manage.py migrate transactions 0000

python manage.py migrate accounts 0000
```

## Previewing Rollback SQL

Before applying a rollback, you can preview the SQL that will be executed using the `--backwards` flag:

### Preview SQL for Rolling Back
```bash
python manage.py sqlmigrate transactions 0001_initial --backwards

python manage.py sqlmigrate accounts 0001_initial --backwards
```

This shows you the exact SQL statements that will run during the rollback without actually executing them.

## Safe Rollback Helper Command

We provide a `safe_rollback` management command that automates the rollback process with safety checks:

### Usage
```bash
python manage.py safe_rollback

python manage.py safe_rollback --accounts-migration 0001_initial --transactions-migration 0001_initial

python manage.py safe_rollback --to-zero

python manage.py safe_rollback --no-backup
```

### What the Command Does
1. Automatically backs up the database (unless `--no-backup` is specified)
2. Checks migration dependencies
3. Rolls back apps in the correct order (transactions first, then accounts)
4. Provides detailed feedback about the rollback process

## Complete Rollback Example

Here's a complete example of safely rolling back all migrations:

```bash
python manage.py showmigrations

python manage.py backup_db

python manage.py sqlmigrate transactions 0001_initial --backwards
python manage.py sqlmigrate accounts 0001_initial --backwards

python manage.py migrate transactions zero
python manage.py migrate accounts zero

python manage.py showmigrations

python manage.py safe_rollback --to-zero
```

## Troubleshooting

### Foreign Key Constraint Errors
If you get foreign key constraint errors, ensure you're rolling back in the correct order:
1. transactions (first)
2. accounts (second)

### Migration Not Found
If Django can't find a migration, check:
```bash
ls accounts/migrations/
ls transactions/migrations/
```

### Restoring from Backup
If something goes wrong, restore from your backup:

```bash
cp db.sqlite3.backup db.sqlite3
```

## Best Practices

1. **Always backup before rollback** - Use `python manage.py backup_db`
2. **Test in development first** - Never roll back production without testing
3. **Preview SQL first** - Use `sqlmigrate --backwards` to see what will happen
4. **Check dependencies** - Understand which migrations depend on others
5. **Follow the correct order** - Roll back transactions before accounts
6. **Verify after rollback** - Use `showmigrations` to confirm the rollback
7. **Document the reason** - Keep notes on why you're rolling back

## Additional Resources

- [Django Migrations Documentation](https://docs.djangoproject.com/en/stable/topics/migrations/)
- [Django Migration Operations](https://docs.djangoproject.com/en/stable/ref/migration-operations/)
