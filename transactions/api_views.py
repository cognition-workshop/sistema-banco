from rest_framework import viewsets, permissions, filters
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from .models import Transaction
from .serializers import TransactionSerializer


class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Transaction.objects.select_related('account__user').all()
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    ordering_fields = ['timestamp', 'amount']
    ordering = ['-timestamp']
    search_fields = ['account__account_no']
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return Transaction.objects.select_related('account__user').all()
        if hasattr(self.request.user, 'account'):
            return Transaction.objects.filter(
                account=self.request.user.account
            ).select_related('account__user')
        return Transaction.objects.none()
