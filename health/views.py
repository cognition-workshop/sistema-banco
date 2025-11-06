from django.http import JsonResponse
from django.db import connection
from django.views import View
from django.conf import settings
import redis
import psutil
import os


class HealthCheckView(View):
    def get(self, request):
        health_status = {
            'status': 'healthy',
            'checks': {}
        }
        
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
            health_status['checks']['database'] = {
                'status': 'healthy',
                'message': 'Database connection successful'
            }
        except Exception as e:
            health_status['status'] = 'unhealthy'
            health_status['checks']['database'] = {
                'status': 'unhealthy',
                'message': str(e)
            }
        
        try:
            redis_client = redis.Redis.from_url(
                settings.CELERY_BROKER_URL,
                decode_responses=True
            )
            redis_client.ping()
            health_status['checks']['redis'] = {
                'status': 'healthy',
                'message': 'Redis connection successful'
            }
        except Exception as e:
            health_status['checks']['redis'] = {
                'status': 'unhealthy',
                'message': str(e)
            }
        
        try:
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            health_status['checks']['disk'] = {
                'status': 'healthy' if disk_percent < 90 else 'warning',
                'usage_percent': disk_percent,
                'message': f'Disk usage at {disk_percent}%'
            }
            if disk_percent >= 90:
                health_status['status'] = 'warning'
        except Exception as e:
            health_status['checks']['disk'] = {
                'status': 'unhealthy',
                'message': str(e)
            }
        
        try:
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            health_status['checks']['memory'] = {
                'status': 'healthy' if memory_percent < 90 else 'warning',
                'usage_percent': memory_percent,
                'message': f'Memory usage at {memory_percent}%'
            }
            if memory_percent >= 90 and health_status['status'] == 'healthy':
                health_status['status'] = 'warning'
        except Exception as e:
            health_status['checks']['memory'] = {
                'status': 'unhealthy',
                'message': str(e)
            }
        
        status_code = 200 if health_status['status'] in ['healthy', 'warning'] else 503
        return JsonResponse(health_status, status=status_code)
