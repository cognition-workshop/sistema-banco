import logging
from django.http import JsonResponse
from django.db import connection
from django.views.generic import TemplateView

logger = logging.getLogger(__name__)


class HomeView(TemplateView):
    template_name = "core/index.html"


def health_check(request):
    """Health check endpoint for monitoring."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")

        return JsonResponse(
            {
                "status": "healthy",
                "database": "ok",
            }
        )
    except Exception as e:
        logger.exception("Health check failed")
        return JsonResponse(
            {"status": "unhealthy", "database": "error", "error": str(e)}, status=503
        )
