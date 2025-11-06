from django.views.generic import TemplateView
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
import time


class HomeView(TemplateView):
    template_name = "core/index.html"


def health_check_view(request):
    """Basic health check - app is running"""
    return JsonResponse(
        {
            "status": "OK",
            "message": "Sistema bancário está funcionando",
            "timestamp": time.time(),
        }
    )


def readiness_check_view(request):
    """Readiness check - all dependencies are working"""
    checks = {"database": False, "redis": False, "overall": False}

    try:
        connection.ensure_connection()
        checks["database"] = True
    except Exception as e:
        checks["database_error"] = str(e)

    try:
        cache.set("health_check", "ok", 10)
        if cache.get("health_check") == "ok":
            checks["redis"] = True
    except Exception as e:
        checks["redis_error"] = str(e)

    checks["overall"] = checks["database"] and checks["redis"]

    status_code = 200 if checks["overall"] else 503

    return JsonResponse(
        {
            "status": "OK" if checks["overall"] else "FAILED",
            "checks": checks,
            "timestamp": time.time(),
        },
        status=status_code,
    )


def handler404(request, exception):
    """Custom 404 handler"""
    from django.shortcuts import render

    return render(request, "errors/404.html", status=404)


def handler500(request):
    """Custom 500 handler"""
    from django.shortcuts import render

    return render(request, "errors/500.html", status=500)


def handler403(request, exception):
    """Custom 403 handler"""
    from django.shortcuts import render

    return render(request, "errors/403.html", status=403)
