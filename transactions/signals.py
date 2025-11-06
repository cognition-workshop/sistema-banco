from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Transaction


@receiver(post_save, sender=Transaction)
def check_fraud_on_transaction(sender, instance, created, **kwargs):
    if created:
        from admin_panel.fraud_detection import FraudDetectionService
        FraudDetectionService.check_transaction(instance)
