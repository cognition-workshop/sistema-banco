import logging
from django.shortcuts import render
from django.db import OperationalError, IntegrityError

logger = logging.getLogger('django')
audit_logger = logging.getLogger('audit')


class ErrorHandlingMiddleware:
    """
    Middleware to catch and log unhandled exceptions
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        """
        Log unhandled exceptions and return user-friendly error pages
        """
        user = request.user if hasattr(request, 'user') else 'Anonymous'
        user_info = str(user) if user else 'Anonymous'

        logger.error(
            f'Unhandled exception for user {user_info} at {request.path}',
            exc_info=True,
            extra={
                'user': user_info,
                'path': request.path,
                'method': request.method,
                'get_params': dict(request.GET),
                'post_params': dict(request.POST) if request.method == 'POST' else {},
            }
        )

        if isinstance(exception, (OperationalError, IntegrityError)):
            logger.error(f'Database error: {str(exception)}')
            return render(request, '500.html', status=500)

        return None
