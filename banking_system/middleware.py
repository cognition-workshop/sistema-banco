import logging
from django.http import JsonResponse
from django.shortcuts import render
from django.conf import settings

logger = logging.getLogger("banking_system")


class ErrorHandlingMiddleware:
    """
    Custom middleware to handle exceptions globally and provide
    user-friendly error messages in Portuguese.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        """
        Handle exceptions that occur during request processing.
        """
        logger.error(
            f"Exception occurred: {str(exception)}",
            extra={
                "user": getattr(request.user, "email", "anonymous"),
                "path": request.path,
                "method": request.method,
                "exception_type": type(exception).__name__,
            },
            exc_info=True,
        )

        if settings.DEBUG:
            return None

        if request.path.startswith("/api/") or request.META.get(
            "HTTP_ACCEPT", ""
        ).startswith("application/json"):
            return JsonResponse(
                {
                    "error": "Ocorreu um erro interno no servidor. Por favor, tente novamente mais tarde.",
                    "details": str(exception) if settings.DEBUG else None,
                },
                status=500,
            )

        context = {
            "error_message": "Ocorreu um erro inesperado. Nossa equipe foi notificada.",
            "support_email": "suporte@banco.com",
        }

        return render(request, "errors/500.html", context, status=500)


class SecurityHeadersMiddleware:
    """
    Add security headers to all responses.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response["X-Content-Type-Options"] = "nosniff"
        response["X-Frame-Options"] = "DENY"
        response["X-XSS-Protection"] = "1; mode=block"
        return response
