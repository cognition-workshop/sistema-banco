from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum
from .models import UserBankAccount, User
from .serializers import UserBankAccountSerializer, UserSerializer
from transactions.models import Transaction
from transactions.serializers import TransactionSerializer


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)


class UserBankAccountViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = UserBankAccount.objects.select_related('user', 'account_type')
    serializer_class = UserBankAccountSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return UserBankAccount.objects.all()
        return UserBankAccount.objects.filter(user=self.request.user)
    
    @action(detail=True, methods=['get'])
    def transactions(self, request, pk=None):
        account = self.get_object()
        transactions = Transaction.objects.filter(account=account).order_by('-timestamp')
        serializer = TransactionSerializer(transactions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def summary(self, request, pk=None):
        account = self.get_object()
        transactions = Transaction.objects.filter(account=account)
        
        summary = {
            'account_number': account.account_no,
            'current_balance': float(account.balance),
            'total_transactions': transactions.count(),
            'total_deposits': float(transactions.filter(
                transaction_type='DEPOSIT'
            ).aggregate(Sum('amount'))['amount__sum'] or 0),
            'total_withdrawals': float(transactions.filter(
                transaction_type='WITHDRAWAL'
            ).aggregate(Sum('amount'))['amount__sum'] or 0),
            'total_interest': float(transactions.filter(
                transaction_type='INTEREST'
            ).aggregate(Sum('amount'))['amount__sum'] or 0),
        }
        
        return Response(summary)
