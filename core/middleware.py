import logging
import time

logger = logging.getLogger("django")


class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()

        logger.info(f"Request: {request.method} {request.path}")

        response = self.get_response(request)

        duration = time.time() - start_time
        logger.info(
            f"Response: {response.status_code} {request.path} ({duration:.2f}s)"
        )

        return response
