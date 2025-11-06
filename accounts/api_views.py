from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import User, BankAccountType, UserBankAccount
from .serializers import (
    UserSerializer, BankAccountTypeSerializer, 
    UserBankAccountSerializer
)


class BankAccountTypeViewSet(viewsets.ModelViewSet):
    """
    API endpoint for bank account types.
    Supports full CRUD operations.
    """
    queryset = BankAccountType.objects.all()
    serializer_class = BankAccountTypeSerializer


class UserBankAccountViewSet(viewsets.ModelViewSet):
    """
    API endpoint for bank accounts.
    Supports full CRUD operations.
    """
    queryset = UserBankAccount.objects.select_related(
        'user', 'account_type'
    ).all()
    serializer_class = UserBankAccountSerializer
    
    @action(detail=True, methods=['get'])
    def balance(self, request, pk=None):
        """Get account balance"""
        account = self.get_object()
        return Response({
            'account_no': account.account_no,
            'balance': account.balance
        })


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint for users.
    Supports full CRUD operations.
    """
    queryset = User.objects.select_related('account', 'address').all()
    serializer_class = UserSerializer
