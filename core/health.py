import logging
import time
import psutil
from django.http import JsonResponse
from django.db import connection
from django.conf import settings
from django.views.decorators.http import require_http_methods

try:
    from redis import Redis

    REDIS_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    REDIS_AVAILABLE = False
    Redis = None

logger = logging.getLogger("banking_system")


def check_database():
    """Check database connectivity."""
    try:
        start_time = time.time()
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        response_time = (time.time() - start_time) * 1000
        return {"status": "healthy", "response_time_ms": round(response_time, 2)}
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return {"status": "unhealthy", "error": str(e)}


def check_redis():
    """Check Redis connectivity."""
    if not REDIS_AVAILABLE:
        return {
            "status": "unavailable",
            "error": "Redis client not available (distutils compatibility issue)",
        }

    try:
        start_time = time.time()
        redis_client = Redis.from_url(settings.CELERY_BROKER_URL)
        redis_client.ping()
        response_time = (time.time() - start_time) * 1000
        return {"status": "healthy", "response_time_ms": round(response_time, 2)}
    except Exception as e:
        logger.error(f"Redis health check failed: {str(e)}")
        return {"status": "unhealthy", "error": str(e)}


def get_system_metrics():
    """Get system performance metrics."""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        return {
            "cpu_usage_percent": cpu_percent,
            "memory": {
                "total_mb": round(memory.total / (1024 * 1024), 2),
                "used_mb": round(memory.used / (1024 * 1024), 2),
                "percent": memory.percent,
            },
            "disk": {
                "total_gb": round(disk.total / (1024 * 1024 * 1024), 2),
                "used_gb": round(disk.used / (1024 * 1024 * 1024), 2),
                "percent": disk.percent,
            },
        }
    except Exception as e:
        logger.error(f"Failed to get system metrics: {str(e)}")
        return {"error": str(e)}


@require_http_methods(["GET"])
def health_check(request):
    """Basic health check endpoint."""
    return JsonResponse(
        {"status": "healthy", "service": "banking-system", "timestamp": time.time()}
    )


@require_http_methods(["GET"])
def health_check_database(request):
    """Database health check endpoint."""
    db_status = check_database()
    status_code = 200 if db_status["status"] == "healthy" else 503

    return JsonResponse(
        {"service": "database", "timestamp": time.time(), **db_status},
        status=status_code,
    )


@require_http_methods(["GET"])
def health_check_redis(request):
    """Redis health check endpoint."""
    redis_status = check_redis()
    status_code = 200 if redis_status["status"] == "healthy" else 503

    return JsonResponse(
        {"service": "redis", "timestamp": time.time(), **redis_status},
        status=status_code,
    )


@require_http_methods(["GET"])
def health_check_detailed(request):
    """Detailed health check with all dependencies and metrics."""
    db_status = check_database()
    redis_status = check_redis()
    system_metrics = get_system_metrics()

    overall_healthy = db_status["status"] == "healthy" and redis_status["status"] in [
        "healthy",
        "unavailable",
    ]

    status_code = 200 if overall_healthy else 503

    return JsonResponse(
        {
            "status": "healthy" if overall_healthy else "unhealthy",
            "service": "banking-system",
            "timestamp": time.time(),
            "checks": {"database": db_status, "redis": redis_status},
            "system_metrics": system_metrics,
        },
        status=status_code,
    )
