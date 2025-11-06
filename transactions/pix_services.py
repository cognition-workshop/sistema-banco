from django.db import transaction
from django.utils import timezone
from decimal import Decimal
import uuid
import qrcode
from io import BytesIO
import base64

from .pix_models import PIXKey, PIXTransaction, PIXQRCode
from .models import Transaction
from .constants import PIX_TRANSFER


class PIXService:
    @staticmethod
    def register_pix_key(user, key_type, key_value):
        """Register a new PIX key for user."""
        if PIXKey.objects.filter(key_value=key_value).exists():
            raise ValueError("Esta chave PIX já está registrada")
        
        pix_key = PIXKey.objects.create(
            user=user,
            key_type=key_type,
            key_value=key_value
        )
        return pix_key
    
    @staticmethod
    @transaction.atomic
    def process_pix_transfer(from_account, to_key_value, amount, description=""):
        """Process a PIX transfer."""
        try:
            to_key = PIXKey.objects.get(key_value=to_key_value, is_active=True)
        except PIXKey.DoesNotExist:
            raise ValueError("Chave PIX não encontrada")
        
        to_account = to_key.user.account
        
        if from_account.balance < amount:
            raise ValueError("Saldo insuficiente")
        
        end_to_end_id = f"E{timezone.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:8]}"
        
        pix_transaction = PIXTransaction.objects.create(
            from_account=from_account,
            to_key=to_key,
            amount=amount,
            end_to_end_id=end_to_end_id,
            description=description,
            status='COMPLETED'
        )
        
        from_account.balance -= amount
        from_account.save(update_fields=['balance'])
        
        to_account.balance += amount
        to_account.save(update_fields=['balance'])
        
        Transaction.objects.create(
            account=from_account,
            amount=-amount,
            balance_after_transaction=from_account.balance,
            transaction_type=PIX_TRANSFER
        )
        
        Transaction.objects.create(
            account=to_account,
            amount=amount,
            balance_after_transaction=to_account.balance,
            transaction_type=PIX_TRANSFER
        )
        
        return pix_transaction
    
    @staticmethod
    def generate_qr_code(pix_key, amount=None, description=""):
        """Generate a PIX QR Code."""
        qr_data = f"PIX:{pix_key.key_value}"
        if amount:
            qr_data += f"|{amount}"
        if description:
            qr_data += f"|{description}"
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        qr_code = PIXQRCode.objects.create(
            pix_key=pix_key,
            amount=amount,
            description=description,
            qr_code_data=qr_code_base64
        )
        
        return qr_code
