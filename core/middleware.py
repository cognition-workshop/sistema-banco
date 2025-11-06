import logging
from django.http import JsonResponse
from django.shortcuts import render
from django.db import IntegrityError
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)


class ExceptionHandlingMiddleware:
    """Middleware to handle exceptions and display user-friendly error pages"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        return self.get_response(request)
    
    def process_exception(self, request, exception):
        """Handle exceptions and return appropriate responses"""
        
        logger.error(
            f"Exception occurred: {type(exception).__name__}",
            exc_info=True,
            extra={
                'request_path': request.path,
                'request_method': request.method,
                'user': request.user.username if request.user.is_authenticated else 'Anonymous'
            }
        )
        
        if isinstance(exception, (IntegrityError, ValidationError)):
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'error': 'A validation error occurred. Please check your input.'
                }, status=400)
            return render(request, '500.html', status=500)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'error': 'An unexpected error occurred.'
            }, status=500)
        
        return render(request, '500.html', status=500)
