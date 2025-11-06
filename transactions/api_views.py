from rest_framework import viewsets
from .models import Transaction
from .serializers import TransactionSerializer


class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Transaction.objects.select_related('account__user', 'account__account_type').all()
    serializer_class = TransactionSerializer
    filterset_fields = ['transaction_type', 'account']
    ordering_fields = ['timestamp', 'amount']
    ordering = ['-timestamp']
