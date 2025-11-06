from django.utils.deprecation import MiddlewareMixin
from .utils import create_audit_log


class AuditMiddleware(MiddlewareMixin):
    """
    Middleware to automatically capture transaction audit logs.
    This is attached to request so views can use it.
    """
    def process_request(self, request):
        request.create_audit_log = lambda account, transaction_type, amount, balance_before, balance_after, **kwargs: create_audit_log(
            request, account, transaction_type, amount, balance_before, balance_after, **kwargs
        )
