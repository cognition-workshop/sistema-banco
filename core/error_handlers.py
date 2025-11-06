import logging
from django.shortcuts import render

logger = logging.getLogger(__name__)


def bad_request(request, exception=None):
    logger.warning(
        f"Bad request: {request.path}",
        extra={
            "user": request.user.email if request.user.is_authenticated else "anonymous"
        },
    )
    return render(request, "errors/400.html", status=400)


def permission_denied(request, exception=None):
    logger.warning(
        f"Permission denied: {request.path}",
        extra={
            "user": request.user.email if request.user.is_authenticated else "anonymous"
        },
    )
    return render(request, "errors/403.html", status=403)


def page_not_found(request, exception=None):
    logger.info(f"Page not found: {request.path}")
    return render(request, "errors/404.html", status=404)


def server_error(request):
    logger.error(
        f"Server error: {request.path}",
        extra={
            "user": request.user.email if request.user.is_authenticated else "anonymous"
        },
    )
    return render(request, "errors/500.html", status=500)
