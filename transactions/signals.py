from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Transaction
from core.fraud_detection import FraudDetector


@receiver(post_save, sender=Transaction)
def check_fraud_on_transaction(sender, instance, created, **kwargs):
    if created:
        FraudDetector.run_all_checks(instance)
