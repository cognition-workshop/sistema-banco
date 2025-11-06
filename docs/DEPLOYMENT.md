# Deployment Guide

## Prerequisites
- Python 3.7+
- PostgreSQL 12+
- Redis 6+
- Nginx (for production)

## Environment Setup

1. Create `.env` file from `.env.example`:
```bash
cp .env.example .env
```

2. Configure environment variables:
```
DEBUG=False
SECRET_KEY=generate-a-strong-secret-key
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DB_NAME=banking_system
DB_USER=postgres
DB_PASSWORD=strong-password
```

## Database Setup

1. Create PostgreSQL database:
```sql
CREATE DATABASE banking_system;
CREATE USER banking_user WITH PASSWORD 'your-password';
GRANT ALL PRIVILEGES ON DATABASE banking_system TO banking_user;
```

2. Run migrations:
```bash
python manage.py migrate --settings=banking_system.settings_prod
```

## Static Files

```bash
python manage.py collectstatic --settings=banking_system.settings_prod
```

## Celery Setup

Start Celery worker:
```bash
celery -A banking_system worker -l info
```

Start Celery beat (for scheduled tasks):
```bash
celery -A banking_system beat -l info
```

## Running in Production

Use gunicorn or uWSGI:
```bash
gunicorn banking_system.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 4 \
  --timeout 120
```

## Health Checks

Monitor application health:
```bash
curl http://localhost:8000/health/
curl http://localhost:8000/readiness/
```

## Security Checklist

- [ ] DEBUG=False in production
- [ ] Strong SECRET_KEY generated
- [ ] ALLOWED_HOSTS configured
- [ ] Database credentials secured
- [ ] SSL/TLS enabled
- [ ] SECURE_* settings configured
- [ ] Firewall configured
- [ ] Regular backups scheduled
