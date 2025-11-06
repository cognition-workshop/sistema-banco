# Database Migration Guide

## Overview
This guide covers the process for safely applying and rolling back database migrations in the banking system.

## Pre-Migration Checklist

Before applying any migrations:

1. **Backup Database**
   - Automatic backups are created in `backups/` directory
   - Manual backup: `cp db.sqlite3 backups/db_backup_manual_$(date +%Y%m%d).sqlite3`

2. **Review Migration Files**
   - Check generated migration files in `<app>/migrations/`
   - Ensure operations are reversible when possible
   - Review data migrations for correctness

3. **Test in Development**
   - Apply migrations in development environment first
   - Run full test suite
   - Verify application functionality

4. **Check Dependencies**
   - Ensure all team members have pulled latest code
   - Verify no conflicting migrations exist

## Applying Migrations

### Using Migration Manager Script (Recommended)

```bash
# Validate migrations
python scripts/migration_manager.py validate

# Apply all pending migrations (creates backup automatically)
python scripts/migration_manager.py apply

# List migration status
python scripts/migration_manager.py list
```

### Manual Migration Process

```bash
# Check for pending migrations
python manage.py showmigrations

# Create backup
cp db.sqlite3 backups/db_backup_$(date +%Y%m%d_%H%M%S).sqlite3

# Apply migrations
python manage.py migrate

# Verify success
python manage.py check
```

## Rolling Back Migrations

### Automatic Rollback

```bash
# Rollback specific app to specific migration
python scripts/migration_manager.py rollback accounts 0003_previous_migration
```

### Manual Rollback

```bash
# Rollback to specific migration
python manage.py migrate accounts 0003_previous_migration

# Rollback all migrations for an app
python manage.py migrate accounts zero
```

## Emergency Procedures

### Complete Database Restore

If migrations cause critical issues:

```bash
# Stop the application
# Restore from backup
cp backups/db_backup_TIMESTAMP.sqlite3 db.sqlite3
# Restart application
```

### Squashing Migrations

For apps with many migrations:

```bash
python manage.py squashmigrations accounts 0001 0010
```

## Production Deployment Checklist

1. ✓ All migrations tested in staging
2. ✓ Database backup created
3. ✓ Rollback plan prepared
4. ✓ Team notified of deployment
5. ✓ Application in maintenance mode (if needed)
6. ✓ Migrations applied
7. ✓ Application tested post-migration
8. ✓ Monitoring for errors
9. ✓ Team notified of completion

## Common Issues and Solutions

### Issue: Migration Conflicts
**Solution:** Use `python manage.py makemigrations --merge` to create merge migration

### Issue: Fake Migration Needed
**Solution:** `python manage.py migrate --fake <app> <migration>` (use with caution)

### Issue: Circular Dependencies
**Solution:** Review migration dependencies and potentially squash migrations

## Best Practices

1. **Always test migrations in development first**
2. **Keep migrations small and focused**
3. **Write reversible migrations when possible**
4. **Document complex data migrations**
5. **Use `RunPython` for data migrations with reverse function**
6. **Never edit applied migrations**
7. **Commit migrations with related code changes**

## Support

For issues with migrations, contact the development team or refer to Django documentation:
https://docs.djangoproject.com/en/3.2/topics/migrations/
