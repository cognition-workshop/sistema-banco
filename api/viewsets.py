from rest_framework import viewsets, filters
from accounts.models import User, UserBankAccount
from transactions.models import Transaction
from .serializers import UserSerializer, AccountSerializer, TransactionSerializer


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['email', 'first_name', 'last_name']


class AccountViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = UserBankAccount.objects.select_related('user', 'account_type').all()
    serializer_class = AccountSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['account_no', 'user__email']


class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Transaction.objects.select_related('account', 'account__user').all()
    serializer_class = TransactionSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['timestamp', 'amount']
    ordering = ['-timestamp']
