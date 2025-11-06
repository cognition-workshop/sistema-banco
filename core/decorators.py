import logging
from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect

logger = logging.getLogger(__name__)


def safe_view(view_func):
    """Decorator para capturar erros em views"""

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        try:
            return view_func(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Erro na view {view_func.__name__}: {str(e)}", exc_info=True)
            messages.error(
                request,
                "Ocorreu um erro ao processar sua solicitação. "
                "Por favor, tente novamente.",
            )
            return redirect("home")

    return wrapper
