from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Transaction
from .serializers import TransactionSerializer


class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Transaction.objects.select_related('account__user', 'account__account_type').all()
    serializer_class = TransactionSerializer
    permission_classes = [permissions.AllowAny]
    
    @action(detail=False, methods=['get'])
    def by_account(self, request):
        account_no = request.query_params.get('account_no')
        if account_no:
            transactions = self.queryset.filter(account__account_no=account_no)
            serializer = self.get_serializer(transactions, many=True)
            return Response(serializer.data)
        return Response({'detail': 'account_no parameter required'}, status=400)
