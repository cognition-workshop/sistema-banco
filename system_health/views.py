import redis
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import connection
from django.http import JsonResponse
from django.views import View
from django.views.generic import TemplateView
from celery import current_app


def check_database():
    """Check database connection status."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return {
            "status": "healthy",
            "message": "Database connection OK",
            "type": "sqlite"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"Database error: {str(e)}",
            "type": "sqlite"
        }


def check_redis():
    """Check Redis connection status."""
    try:
        r = redis.from_url(settings.CELERY_BROKER_URL)
        r.ping()
        return {
            "status": "healthy",
            "message": "Redis connection OK",
            "url": settings.CELERY_BROKER_URL
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"Redis error: {str(e)}",
            "url": settings.CELERY_BROKER_URL
        }


def check_celery():
    """Check Celery worker status."""
    try:
        inspector = current_app.control.inspect()
        active_workers = inspector.active()
        
        if active_workers:
            worker_count = len(active_workers)
            return {
                "status": "healthy",
                "workers": worker_count,
                "message": f"{worker_count} Celery worker(s) active",
                "details": list(active_workers.keys())
            }
        else:
            return {
                "status": "warning",
                "workers": 0,
                "message": "No Celery workers found",
                "details": []
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "workers": 0,
            "message": f"Celery error: {str(e)}",
            "details": []
        }


class AdminRequiredMixin(UserPassesTestMixin):
    """Require staff/admin access."""
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser


class SystemHealthDashboardView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    """Main system health dashboard view."""
    template_name = 'system_health/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'System Health Dashboard'
        return context


class DatabaseStatusView(LoginRequiredMixin, AdminRequiredMixin, View):
    """API endpoint for database status."""
    def get(self, request):
        status = check_database()
        return JsonResponse(status)


class RedisStatusView(LoginRequiredMixin, AdminRequiredMixin, View):
    """API endpoint for Redis status."""
    def get(self, request):
        status = check_redis()
        return JsonResponse(status)


class CeleryStatusView(LoginRequiredMixin, AdminRequiredMixin, View):
    """API endpoint for Celery worker status."""
    def get(self, request):
        status = check_celery()
        return JsonResponse(status)


class PerformanceMetricsView(LoginRequiredMixin, AdminRequiredMixin, View):
    """API endpoint for performance metrics."""
    def get(self, request):
        metrics = {
            "status": "healthy",
            "message": "Basic metrics available",
            "metrics": {
                "database_queries": "Available via Django Debug Toolbar",
                "response_time": "Can be measured via middleware",
                "memory_usage": "Can be measured via system tools"
            }
        }
        return JsonResponse(metrics)
