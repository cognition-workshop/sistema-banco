import logging
import time
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger('banking_system')


class PerformanceMonitoringMiddleware(MiddlewareMixin):
    
    def process_request(self, request):
        request._start_time = time.time()
        
    def process_response(self, request, response):
        if hasattr(request, '_start_time'):
            duration = time.time() - request._start_time
            
            log_data = {
                'method': request.method,
                'path': request.path,
                'status_code': response.status_code,
                'duration_ms': round(duration * 1000, 2),
                'user': str(request.user) if hasattr(request, 'user') and request.user.is_authenticated else 'Anonymous',
            }
            
            log_message = (
                f"Request: {log_data['method']} {log_data['path']} | "
                f"Status: {log_data['status_code']} | "
                f"Duration: {log_data['duration_ms']}ms | "
                f"User: {log_data['user']}"
            )
            
            if response.status_code >= 500:
                logger.error(log_message)
            elif response.status_code >= 400:
                logger.warning(log_message)
            elif duration > 1.0:
                logger.warning(f"SLOW REQUEST: {log_message}")
            else:
                logger.info(log_message)
        
        return response
