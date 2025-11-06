from django.http import JsonResponse
from django.db import connection


def health_check(request):
    return JsonResponse({
        'status': 'healthy',
        'service': 'application'
    }, status=200)


def health_check_db(request):
    try:
        connection.ensure_connection()
        return JsonResponse({
            'status': 'healthy',
            'service': 'database',
            'details': 'Database connection successful'
        }, status=200)
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'service': 'database',
            'details': str(e)
        }, status=503)


def health_check_redis(request):
    try:
        import redis
        redis_client = redis.Redis(host='localhost', port=6379)
        redis_client.ping()
        return JsonResponse({
            'status': 'healthy',
            'service': 'redis',
            'details': 'Redis connection successful'
        }, status=200)
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'service': 'redis',
            'details': str(e)
        }, status=503)


def health_check_celery(request):
    try:
        from banking_system.celery import app
        inspector = app.control.inspect()
        ping_result = inspector.ping()
        
        if ping_result and len(ping_result) > 0:
            worker_count = len(ping_result)
            return JsonResponse({
                'status': 'healthy',
                'service': 'celery',
                'details': f'{worker_count} worker(s) active'
            }, status=200)
        else:
            return JsonResponse({
                'status': 'unhealthy',
                'service': 'celery',
                'details': 'No active workers found'
            }, status=503)
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'service': 'celery',
            'details': str(e)
        }, status=503)
