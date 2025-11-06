from .models import AuditLog


def create_audit_log(request, account, transaction_type, amount, balance_before, balance_after, **kwargs):
    """
    Create an audit log entry for a transaction.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip_address = x_forwarded_for.split(',')[0]
    else:
        ip_address = request.META.get('REMOTE_ADDR', '0.0.0.0')
    
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    audit_log = AuditLog.objects.create(
        user=request.user if request.user.is_authenticated else None,
        account=account,
        transaction_type=transaction_type,
        amount=amount,
        balance_before=balance_before,
        balance_after=balance_after,
        ip_address=ip_address,
        user_agent=user_agent,
        additional_data=kwargs
    )
    
    return audit_log
