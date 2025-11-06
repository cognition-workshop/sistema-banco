import json
import logging
from datetime import datetime


class JsonFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging in production
    """
    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        if hasattr(record, 'user_email'):
            log_data['user_email'] = record.user_email
        if hasattr(record, 'account_no'):
            log_data['account_no'] = record.account_no
        if hasattr(record, 'amount'):
            log_data['amount'] = str(record.amount)
        if hasattr(record, 'transaction_type'):
            log_data['transaction_type'] = record.transaction_type
        if hasattr(record, 'balance_after'):
            log_data['balance_after'] = str(record.balance_after)
        
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)
