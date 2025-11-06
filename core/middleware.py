import time
import logging
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class PerformanceMonitoringMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request._start_time = time.time()
        return None

    def process_response(self, request, response):
        if hasattr(request, "_start_time"):
            duration = time.time() - request._start_time

            if duration > 1.0:
                logger.warning(
                    f"Slow request: {request.method} {request.path}",
                    extra={
                        "duration": duration,
                        "user": request.user.email
                        if request.user.is_authenticated
                        else "anonymous",
                        "status_code": response.status_code,
                    },
                )

            response["X-Request-Duration"] = f"{duration:.3f}s"

        return response


class RequestLoggingMiddleware(MiddlewareMixin):
    def process_request(self, request):
        logger.info(
            f"Request: {request.method} {request.path}",
            extra={
                "user": request.user.email
                if request.user.is_authenticated
                else "anonymous",
                "ip": self.get_client_ip(request),
            },
        )
        return None

    @staticmethod
    def get_client_ip(request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip
