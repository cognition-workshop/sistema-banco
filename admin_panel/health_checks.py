import psutil
from django.db import connection
from django.core.cache import cache
from celery import current_app
from datetime import datetime


def check_database_health():
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return {'status': 'healthy', 'message': 'Database connection successful'}
    except Exception as e:
        return {'status': 'unhealthy', 'message': str(e)}


def check_redis_health():
    try:
        cache.set('health_check', 'ok', 10)
        result = cache.get('health_check')
        if result == 'ok':
            return {'status': 'healthy', 'message': 'Redis connection successful'}
        return {'status': 'unhealthy', 'message': 'Redis test failed'}
    except Exception as e:
        return {'status': 'unhealthy', 'message': str(e)}


def check_celery_health():
    try:
        inspector = current_app.control.inspect()
        stats = inspector.stats()
        if stats:
            return {'status': 'healthy', 'message': 'Celery workers active', 'workers': len(stats)}
        return {'status': 'unhealthy', 'message': 'No Celery workers found'}
    except Exception as e:
        return {'status': 'unhealthy', 'message': str(e)}


def get_system_metrics():
    return {
        'cpu_percent': psutil.cpu_percent(interval=1),
        'memory_percent': psutil.virtual_memory().percent,
        'disk_percent': psutil.disk_usage('/').percent,
        'timestamp': datetime.now().isoformat()
    }
