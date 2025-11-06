from django.utils import timezone
from .models import AuditLog
from .constants import (
    DEPOSIT_ATTEMPT,
    DEPOSIT_SUCCESS,
    WITHDRAW_ATTEMPT,
    WITHDRAW_SUCCESS,
    INTEREST_CALCULATION,
    TRANSACTION_MODIFICATION_ATTEMPT,
)


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_user_agent(request):
    return request.META.get('HTTP_USER_AGENT', '')


def create_audit_log(
    action_type,
    success=True,
    user=None,
    transaction=None,
    amount=None,
    error_message=None,
    ip_address=None,
    user_agent=None,
    additional_data=None,
    request=None
):
    try:
        if request:
            if not ip_address:
                ip_address = get_client_ip(request)
            if not user_agent:
                user_agent = get_user_agent(request)
            if not user and hasattr(request, 'user') and request.user.is_authenticated:
                user = request.user
        
        audit_log = AuditLog.objects.create(
            action_type=action_type,
            success=success,
            user=user,
            transaction=transaction,
            amount=amount,
            error_message=error_message,
            ip_address=ip_address,
            user_agent=user_agent,
            additional_data=additional_data or {}
        )
        return audit_log
    except Exception as e:
        print(f"Failed to create audit log: {e}")
        return None
