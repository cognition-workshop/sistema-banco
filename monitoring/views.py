from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.db import connection
from django.conf import settings
import redis


@method_decorator(staff_member_required, name='dispatch')
class SystemHealthView(TemplateView):
    template_name = 'admin/system_health.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            connection.ensure_connection()
            context['db_status'] = 'Connected'
            context['db_healthy'] = True
        except Exception as e:
            context['db_status'] = f'Error: {str(e)}'
            context['db_healthy'] = False
        
        try:
            r = redis.from_url(settings.CELERY_BROKER_URL)
            r.ping()
            context['redis_status'] = 'Connected'
            context['redis_healthy'] = True
        except Exception as e:
            context['redis_status'] = f'Error: {str(e)}'
            context['redis_healthy'] = False
        
        context['system_healthy'] = context['db_healthy'] and context['redis_healthy']
        
        return context
