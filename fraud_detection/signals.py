from django.db.models.signals import post_save
from django.dispatch import receiver
from transactions.models import Transaction
from .services import FraudDetectionService
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Transaction)
def check_transaction_for_fraud(sender, instance, created, **kwargs):
    if created and instance.transaction_type in ['WITHDRAWAL', 'DEPOSIT']:
        try:
            alerts = FraudDetectionService.check_transaction(instance)
            if alerts:
                logger.warning(f'{len(alerts)} fraud alerts created for transaction {instance.id}')
        except Exception as e:
            logger.error(f'Error checking transaction {instance.id} for fraud: {str(e)}')
