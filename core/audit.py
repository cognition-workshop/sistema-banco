from .models import AuditLog
import threading

_thread_locals = threading.local()


def get_current_request():
    """Get the current request from thread-local storage."""
    return getattr(_thread_locals, 'request', None)


def set_current_request(request):
    """Set the current request in thread-local storage."""
    _thread_locals.request = request


class AuditLogger:
    """Utility class for audit logging."""
    
    @staticmethod
    def log_action(user, action, resource_type, resource_id, details=None):
        """Log an audit action."""
        request = get_current_request()
        ip_address = None
        
        if request:
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0]
            else:
                ip_address = request.META.get('REMOTE_ADDR')
        
        AuditLog.objects.create(
            user=user,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id),
            ip_address=ip_address,
            details=details or {}
        )
    
    @staticmethod
    def log_transaction(user, transaction, transaction_type):
        """Log a transaction."""
        AuditLogger.log_action(
            user=user,
            action=transaction_type,
            resource_type='Transaction',
            resource_id=transaction.id,
            details={
                'amount': str(transaction.amount),
                'balance_after': str(transaction.balance_after_transaction)
            }
        )
    
    @staticmethod
    def log_pix_transfer(user, pix_transaction):
        """Log a PIX transfer."""
        AuditLogger.log_action(
            user=user,
            action='PIX_TRANSFER',
            resource_type='PIXTransaction',
            resource_id=pix_transaction.id,
            details={
                'amount': str(pix_transaction.amount),
                'end_to_end_id': pix_transaction.end_to_end_id,
                'to_key': pix_transaction.to_key.key_value
            }
        )
    
    @staticmethod
    def log_pix_key_registration(user, pix_key):
        """Log PIX key registration."""
        AuditLogger.log_action(
            user=user,
            action='PIX_REGISTER_KEY',
            resource_type='PIXKey',
            resource_id=pix_key.id,
            details={
                'key_type': pix_key.key_type,
                'key_value': pix_key.key_value
            }
        )
