from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import Transaction
from .audit import create_audit_log
from .constants import TRANSACTION_MODIFICATION_ATTEMPT


@receiver(pre_save, sender=Transaction)
def log_transaction_modification_attempt(sender, instance, **kwargs):
    if instance.pk:
        try:
            original = Transaction.objects.get(pk=instance.pk)
            
            modified_fields = []
            for field in ['amount', 'balance_after_transaction', 'transaction_type', 'account_id']:
                original_value = getattr(original, field)
                new_value = getattr(instance, field)
                if original_value != new_value:
                    modified_fields.append(field)
            
            if modified_fields:
                create_audit_log(
                    action_type=TRANSACTION_MODIFICATION_ATTEMPT,
                    success=False,
                    transaction=original,
                    error_message=f"Attempt to modify immutable transaction. Fields: {', '.join(modified_fields)}",
                    additional_data={
                        'modified_fields': modified_fields,
                        'original_pk': instance.pk
                    }
                )
        except Transaction.DoesNotExist:
            pass
        except Exception as e:
            print(f"Error in transaction modification signal: {e}")
