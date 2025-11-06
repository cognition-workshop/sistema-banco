import time
import logging
import psutil
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger('monitoring')


class PerformanceMonitoringMiddleware(MiddlewareMixin):
    
    def process_request(self, request):
        request._start_time = time.time()
        request._start_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
    def process_response(self, request, response):
        if hasattr(request, '_start_time'):
            duration = time.time() - request._start_time
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024
            memory_used = end_memory - request._start_memory if hasattr(request, '_start_memory') else 0
            
            logger.info(
                'Request completed',
                extra={
                    'method': request.method,
                    'path': request.path,
                    'status_code': response.status_code,
                    'duration_ms': round(duration * 1000, 2),
                    'memory_used_mb': round(memory_used, 2),
                    'user': str(request.user) if hasattr(request, 'user') else 'anonymous'
                }
            )
        return response
