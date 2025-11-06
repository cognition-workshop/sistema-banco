from rest_framework import viewsets
from django.contrib.auth import get_user_model
from .models import Transaction
from .serializers import TransactionSerializer


User = get_user_model()


class TransactionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for transactions.
    Supports full CRUD operations.
    """
    serializer_class = TransactionSerializer
    
    def get_queryset(self):
        demo_user = User.objects.filter(email='demo@example.com').first()
        if demo_user and hasattr(demo_user, 'account'):
            return Transaction.objects.filter(
                account=demo_user.account
            ).select_related('account').order_by('-timestamp')
        return Transaction.objects.none()
