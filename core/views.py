import logging
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.db import connection

logger = logging.getLogger(__name__)


class HomeView(TemplateView):
    template_name = 'core/index.html'


def health_check(request):
    """Health check endpoint for monitoring"""
    try:
        connection.ensure_connection()
        
        from django_celery_beat.models import PeriodicTask
        PeriodicTask.objects.first()
        
        logger.info("Health check passed")
        return JsonResponse({'status': 'healthy'}, status=200)
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}", exc_info=True)
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e)
        }, status=503)
