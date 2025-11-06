from django.views.generic import TemplateView
from django.http import JsonResponse
from django.views import View
from django.db import connection
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)


class HomeView(TemplateView):
    template_name = 'core/index.html'


class HealthCheckView(View):
    def get(self, request):
        health = {'status': 'healthy', 'checks': {}}
        
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            health['checks']['database'] = 'healthy'
        except Exception as e:
            health['status'] = 'unhealthy'
            health['checks']['database'] = str(e)
            logger.error(f"Database health check failed: {e}")
        
        try:
            cache.set('health', 'ok', 10)
            if cache.get('health') == 'ok':
                health['checks']['cache'] = 'healthy'
        except Exception as e:
            health['status'] = 'unhealthy'
            health['checks']['cache'] = str(e)
        
        status_code = 200 if health['status'] == 'healthy' else 503
        return JsonResponse(health, status=status_code)
