from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Transaction
from .serializers import TransactionSerializer
from .constants import DEPOSIT, WITHDRAWAL


class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Transaction.objects.select_related('account__user')
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['transaction_type', 'timestamp']
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return self.queryset
        if hasattr(self.request.user, 'account'):
            return self.queryset.filter(account=self.request.user.account)
        return self.queryset.none()
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        qs = self.get_queryset()
        return Response({
            'total_transactions': qs.count(),
            'total_deposits': qs.filter(transaction_type=DEPOSIT).count(),
            'total_withdrawals': qs.filter(transaction_type=WITHDRAWAL).count(),
            'latest_balance': request.user.balance if hasattr(request.user, 'account') else 0,
        })
