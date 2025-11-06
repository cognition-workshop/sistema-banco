from rest_framework import viewsets, permissions
from rest_framework.response import Response
from .models import Transaction
from .serializers import TransactionSerializer, TransactionCreateSerializer


class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return Transaction.objects.all().select_related('account__user')
        return Transaction.objects.filter(
            account__user=self.request.user
        ).select_related('account')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return TransactionCreateSerializer
        return TransactionSerializer
