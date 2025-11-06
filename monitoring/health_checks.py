from health_check.backends import BaseHealthCheckBackend
from health_check.exceptions import ServiceUnavailable
from transactions.models import Transaction


class TransactionSystemHealthCheck(BaseHealthCheckBackend):
    
    critical_service = True
    
    def check_status(self):
        try:
            count = Transaction.objects.count()
            self.add_metric('transaction_count', count)
        except Exception as e:
            self.add_error(ServiceUnavailable(f"Transaction system error: {str(e)}"))
    
    def identifier(self):
        return "Transaction System"
