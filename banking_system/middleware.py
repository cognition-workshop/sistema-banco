import logging
import traceback
from django.http import JsonResponse
from django.shortcuts import render
from django.conf import settings

logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
            return response
        except Exception as e:
            return self.handle_exception(request, e)

    def handle_exception(self, request, exception):
        logger.error(
            'Unhandled exception',
            exc_info=True,
            extra={
                'request_path': request.path,
                'request_method': request.method,
                'user': str(request.user) if hasattr(request, 'user') else 'Anonymous',
            }
        )
        
        if settings.DEBUG:
            raise exception
        
        if request.accepts('application/json'):
            return JsonResponse({
                'error': 'An unexpected error occurred',
                'detail': str(exception) if settings.DEBUG else 'Please try again later'
            }, status=500)
        
        return render(request, 'errors/500.html', {
            'error_message': str(exception) if settings.DEBUG else None
        }, status=500)

    def process_exception(self, request, exception):
        return self.handle_exception(request, exception)
