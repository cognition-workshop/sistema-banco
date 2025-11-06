from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import Transaction
from .serializers import TransactionSerializer
from .constants import DEPOSIT, WITHDRAWAL


class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Transaction.objects.select_related('account').all()
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            if hasattr(self.request.user, 'account'):
                queryset = queryset.filter(account=self.request.user.account)
            else:
                queryset = queryset.none()
        
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        if date_from and date_to:
            queryset = queryset.filter(timestamp__date__range=[date_from, date_to])
        
        return queryset
    
    @action(detail=False, methods=['post'])
    def deposit(self, request):
        if not hasattr(request.user, 'account'):
            return Response({'error': 'User has no bank account'}, status=status.HTTP_400_BAD_REQUEST)
        
        amount = request.data.get('amount')
        if not amount or float(amount) < 10:
            return Response({'error': 'Minimum deposit amount is 10'}, status=status.HTTP_400_BAD_REQUEST)
        
        account = request.user.account
        account.balance += float(amount)
        account.save()
        
        transaction = Transaction.objects.create(
            account=account,
            amount=amount,
            balance_after_transaction=account.balance,
            transaction_type=DEPOSIT
        )
        
        serializer = self.get_serializer(transaction)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'])
    def withdraw(self, request):
        if not hasattr(request.user, 'account'):
            return Response({'error': 'User has no bank account'}, status=status.HTTP_400_BAD_REQUEST)
        
        amount = request.data.get('amount')
        if not amount or float(amount) < 10:
            return Response({'error': 'Minimum withdrawal amount is 10'}, status=status.HTTP_400_BAD_REQUEST)
        
        account = request.user.account
        if float(amount) > account.account_type.maximum_withdrawal_amount:
            return Response({'error': f'Maximum withdrawal amount is {account.account_type.maximum_withdrawal_amount}'}, status=status.HTTP_400_BAD_REQUEST)
        
        account.balance -= float(amount)
        account.save()
        
        transaction = Transaction.objects.create(
            account=account,
            amount=amount,
            balance_after_transaction=account.balance,
            transaction_type=WITHDRAWAL
        )
        
        serializer = self.get_serializer(transaction)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
