import logging
from django.http import JsonResponse

logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware:
    """Global error handling middleware for consistent error responses."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
            return response
        except Exception:
            logger.exception(
                "Unhandled exception",
                extra={
                    "user_id": (
                        request.user.id if request.user.is_authenticated else None
                    ),
                    "path": request.path,
                    "method": request.method,
                },
            )
            return JsonResponse(
                {
                    "error": "Ocorreu um erro interno. Por favor, tente novamente mais tarde."
                },
                status=500,
            )
