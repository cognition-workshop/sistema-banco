from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from accounts.models import User, UserBankAccount
from transactions.models import Transaction
from .serializers import (
    UserSerializer, 
    UserBankAccountSerializer, 
    TransactionSerializer
)
from .permissions import IsAccountOwnerOrAdmin, IsAdminUser


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing users. Only accessible by admin users.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]


class UserBankAccountViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing bank accounts. Users can only see their own accounts.
    """
    queryset = UserBankAccount.objects.select_related('user', 'account_type')
    serializer_class = UserBankAccountSerializer
    permission_classes = [permissions.IsAuthenticated, IsAccountOwnerOrAdmin]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return super().get_queryset()
        return super().get_queryset().filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        Get the current user's bank account.
        """
        try:
            account = UserBankAccount.objects.select_related(
                'user', 'account_type'
            ).get(user=request.user)
            serializer = self.get_serializer(account)
            return Response(serializer.data)
        except UserBankAccount.DoesNotExist:
            return Response(
                {'detail': 'Bank account not found.'}, 
                status=status.HTTP_404_NOT_FOUND
            )


class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing transactions. Users can only see their own transactions.
    """
    queryset = Transaction.objects.select_related('account__user')
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated, IsAccountOwnerOrAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['transaction_type', 'timestamp']
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return super().get_queryset()
        return super().get_queryset().filter(account__user=self.request.user)
