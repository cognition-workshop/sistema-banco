import logging
import traceback
from django.http import JsonResponse
from django.shortcuts import render
from django.conf import settings

logger = logging.getLogger("banking_system")


class ErrorHandlingMiddleware:
    """
    Middleware personalizado para capturar e tratar todas as exceções
    com mensagens amigáveis em português brasileiro.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        """
        Processa exceções e retorna respostas amigáveis ao usuário.
        """
        logger.error(
            f"Exceção capturada: {type(exception).__name__}",
            exc_info=True,
            extra={
                "request_path": request.path,
                "request_method": request.method,
                "user": request.user.email if request.user.is_authenticated else "Anônimo",
                "ip_address": self.get_client_ip(request),
            },
        )

        if "transaction" in request.path.lower() or "account" in request.path.lower():
            error_message = "Ocorreu um erro ao processar sua transação. Por favor, tente novamente ou contate o suporte."
        else:
            error_message = "Ocorreu um erro inesperado. Por favor, tente novamente mais tarde."

        if settings.DEBUG:
            return None

        context = {
            "error_message": error_message,
            "error_type": type(exception).__name__,
        }

        return render(request, "500.html", context, status=500)

    @staticmethod
    def get_client_ip(request):
        """Obtém o IP do cliente."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip
