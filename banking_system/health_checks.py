import logging
import redis
import shutil
from django.db import connection
from django.http import JsonResponse
from django.conf import settings
from celery import Celery

logger = logging.getLogger("banking_system")


def health_check(request):
    """
    Endpoint de health check que verifica:
    - Conexão com banco de dados
    - Conexão com Redis
    - Status do Celery worker
    - Espaço em disco disponível
    """
    health_status = {"status": "healthy", "checks": {}}

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        health_status["checks"]["database"] = {"status": "healthy", "message": "Conexão com banco de dados OK"}
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "message": f"Erro na conexão com banco de dados: {str(e)}",
        }
        logger.error(f"Health check - Database error: {str(e)}")

    try:
        redis_client = redis.Redis.from_url(settings.CELERY_BROKER_URL)
        redis_client.ping()
        health_status["checks"]["redis"] = {"status": "healthy", "message": "Conexão com Redis OK"}
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["redis"] = {"status": "unhealthy", "message": f"Erro na conexão com Redis: {str(e)}"}
        logger.error(f"Health check - Redis error: {str(e)}")

    try:
        app = Celery("banking_system")
        app.config_from_object("django.conf:settings", namespace="CELERY")
        inspect = app.control.inspect()
        stats = inspect.stats()

        if stats:
            health_status["checks"]["celery"] = {
                "status": "healthy",
                "message": "Celery workers ativos",
                "workers": len(stats),
            }
        else:
            health_status["status"] = "degraded"
            health_status["checks"]["celery"] = {"status": "degraded", "message": "Nenhum Celery worker ativo"}
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["checks"]["celery"] = {"status": "degraded", "message": f"Não foi possível verificar Celery: {str(e)}"}
        logger.warning(f"Health check - Celery warning: {str(e)}")

    try:
        disk_usage = shutil.disk_usage("/")
        free_percent = (disk_usage.free / disk_usage.total) * 100

        if free_percent > 10:
            health_status["checks"]["disk_space"] = {
                "status": "healthy",
                "message": f"Espaço em disco: {free_percent:.1f}% disponível",
                "free_gb": round(disk_usage.free / (1024**3), 2),
            }
        else:
            health_status["status"] = "degraded"
            health_status["checks"]["disk_space"] = {
                "status": "degraded",
                "message": f"Espaço em disco baixo: {free_percent:.1f}% disponível",
                "free_gb": round(disk_usage.free / (1024**3), 2),
            }
    except Exception as e:
        health_status["checks"]["disk_space"] = {
            "status": "unknown",
            "message": f"Não foi possível verificar espaço em disco: {str(e)}",
        }

    status_code = 200 if health_status["status"] == "healthy" else 503

    return JsonResponse(health_status, status=status_code)


def readiness_check(request):
    """
    Endpoint de readiness check - verifica se a aplicação está pronta para receber tráfego.
    """
    return JsonResponse({"status": "ready"})


def liveness_check(request):
    """
    Endpoint de liveness check - verifica se a aplicação está rodando.
    """
    return JsonResponse({"status": "alive"})
