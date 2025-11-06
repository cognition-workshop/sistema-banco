from django.db.models.signals import post_save
from django.dispatch import receiver
from transactions.models import Transaction
from .tasks import detect_fraud_for_transaction


@receiver(post_save, sender=Transaction)
def check_fraud_on_transaction(sender, instance, created, **kwargs):
    if created:
        detect_fraud_for_transaction.delay(instance.id)
