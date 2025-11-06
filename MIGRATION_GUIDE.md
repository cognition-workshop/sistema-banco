# Database Migration Guide

## Overview
This guide explains how to safely manage database migrations for the banking system.

## Migration Strategy

### 1. Development Migrations

```bash
# Create new migration (important-comment)
python manage.py makemigrations

# Review migration file before applying (important-comment)
cat accounts/migrations/0XXX_migration_name.py

# Apply migration (important-comment)
python manage.py migrate

# Test rollback (important-comment)
python manage.py migrate accounts 0XXX
```

### 2. Production Migrations

**Pre-deployment checklist:**
- [ ] All migrations tested in staging environment
- [ ] Database backup created
- [ ] Rollback plan documented
- [ ] Downtime window scheduled (if required)
- [ ] Team notified

**Deployment process:**
```bash
# 1. Backup database (important-comment)
pg_dump banking_system > backup_$(date +%Y%m%d_%H%M%S).sql

# 2. Apply migrations (important-comment)
python manage.py migrate --noinput

# 3. Verify migration (important-comment)
python manage.py showmigrations

# 4. Test critical paths (important-comment)
python manage.py test
```

**Rollback process:**
```bash
# 1. Rollback to previous migration (important-comment)
python manage.py migrate accounts 0XXX

# 2. Restore database if needed (important-comment)
psql banking_system < backup_YYYYMMDD_HHMMSS.sql

# 3. Verify system health (important-comment)
curl http://localhost:8000/health/
```

### 3. Incremental Migrations for Custom User Model

When modifying the custom User model, always use incremental migrations:

```python
# BAD: Changing field directly (important-comment)
class User(AbstractUser):
    email = models.EmailField(unique=True, max_length=100)

# GOOD: Create separate migration (important-comment)
# Step 1: Add new field (important-comment)
class User(AbstractUser):
    email_new = models.EmailField(unique=True, max_length=100)

# Step 2: Data migration to copy data (important-comment)
# Step 3: Remove old field and rename new field (important-comment)
```

## Migration Best Practices

1. **Never squash migrations** containing custom User model changes
2. **Always test migrations** with production-like data volume
3. **Document complex migrations** with comments
4. **Use RunPython** for data migrations, not raw SQL
5. **Keep migrations small** - one logical change per migration
6. **Version control** all migration files

## Troubleshooting

### Issue: Migration conflicts
```bash
python manage.py makemigrations --merge
```

### Issue: Fake migration needed
```bash
python manage.py migrate --fake accounts 0XXX
```

### Issue: Reset migrations (development only!)
```bash
# WARNING: This will lose all data (important-comment)
python manage.py migrate accounts zero
rm accounts/migrations/0*.py
python manage.py makemigrations accounts
python manage.py migrate
```
