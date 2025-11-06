from celery import shared_task
from .fraud_detector import FraudDetector
from transactions.models import Transaction


@shared_task
def detect_fraud_for_transaction(transaction_id):
    try:
        transaction = Transaction.objects.get(id=transaction_id)
        detector = FraudDetector()
        alerts = detector.check_transaction(transaction)
        return len(alerts)
    except Transaction.DoesNotExist:
        return 0


@shared_task
def cleanup_old_health_metrics():
    from django.utils import timezone
    from datetime import timedelta
    from .models import SystemHealthMetric
    
    threshold = timezone.now() - timedelta(days=30)
    deleted_count, _ = SystemHealthMetric.objects.filter(timestamp__lt=threshold).delete()
    return deleted_count
