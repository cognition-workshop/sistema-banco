# Migration Guide: Sistema Banco Technology Stack Modernization

## Overview
This guide covers the migration from the old technology stack to the modernized version.

## Changes Summary

### 1. Django Upgrade (3.2 → 5.0)
- Updated to Django 5.0.9
- Added `DEFAULT_AUTO_FIELD` setting
- All models are compatible with Django 5.0

### 2. Database Migration (SQLite → PostgreSQL)
**Setup PostgreSQL:**
```bash
# Using Docker
docker-compose up -d postgres

# Or install PostgreSQL locally
# Ubuntu/Debian:
sudo apt-get install postgresql postgresql-contrib

# macOS:
brew install postgresql
```

**Migrate Data:**
```bash
# 1. Dump data from SQLite
python manage.py dumpdata --natural-foreign --natural-primary \
  --exclude contenttypes --exclude auth.permission > datadump.json

# 2. Update settings.py with PostgreSQL configuration

# 3. Create new database and run migrations
python manage.py migrate

# 4. Load data into PostgreSQL
python manage.py loaddata datadump.json
```

### 3. Redis Cache Setup
```bash
# Using Docker
docker-compose up -d redis

# Or install Redis locally
# Ubuntu/Debian:
sudo apt-get install redis-server

# macOS:
brew install redis
```

### 4. Frontend Build Setup
```bash
# Install dependencies
npm install

# Build Tailwind CSS
npm run build:css

# Or watch for changes during development
npm run watch:css
```

### 5. Django REST Framework API
New API endpoints available at `/api/`:
- `/api/users/` - User information
- `/api/accounts/` - Bank account information
- `/api/transactions/` - Transaction history

All endpoints require authentication.

### 6. HTMX Integration
- jQuery has been removed
- HTMX is now used for dynamic interactions
- Date filtering in transaction reports uses HTML5 date inputs

## Installation Steps

1. **Install Python dependencies:**
```bash
pip install -r requirements.txt
```

2. **Set up environment variables:**
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Start database and cache services:**
```bash
docker-compose up -d
```

4. **Run migrations:**
```bash
python manage.py migrate
```

5. **Build frontend assets:**
```bash
npm install
npm run build:css
```

6. **Collect static files:**
```bash
python manage.py collectstatic --noinput
```

7. **Run the development server:**
```bash
python manage.py runserver
```

## Testing the Changes

1. **Registration:** Create a new user account
2. **Login:** Sign in with your credentials
3. **Deposit:** Make a deposit to your account
4. **Withdraw:** Withdraw money from your account
5. **Transaction Report:** View your transaction history with date filtering
6. **API:** Test API endpoints at `/api/`

## Troubleshooting

### PostgreSQL Connection Issues
- Ensure PostgreSQL is running: `docker-compose ps`
- Check credentials in .env match docker-compose.yml
- Verify port 5432 is not in use: `lsof -i :5432`

### Redis Connection Issues
- Ensure Redis is running: `docker-compose ps`
- Check connection: `redis-cli ping`

### Tailwind CSS Not Loading
- Run `npm run build:css` to build CSS
- Ensure static files are collected: `python manage.py collectstatic`
- Check that `STATIC_URL` and `STATIC_ROOT` are configured in settings.py

### HTMX Not Working
- Check browser console for JavaScript errors
- Ensure HTMX script is loaded in base.html
- Verify `hx-*` attributes are correctly set in templates
