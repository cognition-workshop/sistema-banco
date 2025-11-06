import logging
from django.views.generic import TemplateView
from django.views import View
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
from celery import current_app

logger = logging.getLogger(__name__)


class HomeView(TemplateView):
    template_name = 'core/index.html'


class HealthCheckView(View):
    def get(self, request):
        """Comprehensive health check endpoint"""
        health_status = {
            'status': 'healthy',
            'checks': {}
        }
        
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            health_status['checks']['database'] = {'status': 'healthy'}
        except Exception as e:
            health_status['status'] = 'unhealthy'
            health_status['checks']['database'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
        
        try:
            cache.set('health_check', 'ok', 10)
            assert cache.get('health_check') == 'ok'
            health_status['checks']['cache'] = {'status': 'healthy'}
        except Exception as e:
            health_status['status'] = 'unhealthy'
            health_status['checks']['cache'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
        
        try:
            inspect = current_app.control.inspect()
            stats = inspect.stats()
            if stats:
                health_status['checks']['celery_worker'] = {'status': 'healthy'}
            else:
                health_status['status'] = 'degraded'
                health_status['checks']['celery_worker'] = {
                    'status': 'unhealthy',
                    'error': 'No workers available'
                }
        except Exception as e:
            health_status['status'] = 'degraded'
            health_status['checks']['celery_worker'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
        
        status_code = 200 if health_status['status'] == 'healthy' else 503
        return JsonResponse(health_status, status=status_code)


class ReadinessCheckView(View):
    """Lightweight check for container orchestration"""
    def get(self, request):
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            return JsonResponse({'status': 'ready'})
        except Exception as e:
            return JsonResponse({'status': 'not ready', 'error': str(e)}, status=503)


class LivenessCheckView(View):
    """Simple check that application is running"""
    def get(self, request):
        return JsonResponse({'status': 'alive'})
