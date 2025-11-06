from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import User, UserBankAccount, BankAccountType
from .serializers import UserSerializer, UserBankAccountSerializer, BankAccountTypeSerializer


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]
    
    @action(detail=True, methods=['get'])
    def account(self, request, pk=None):
        user = self.get_object()
        if hasattr(user, 'account'):
            serializer = UserBankAccountSerializer(user.account)
            return Response(serializer.data)
        return Response({'detail': 'No account found'}, status=404)


class BankAccountTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = BankAccountType.objects.all()
    serializer_class = BankAccountTypeSerializer
    permission_classes = [permissions.AllowAny]


class UserBankAccountViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = UserBankAccount.objects.select_related('user', 'account_type').all()
    serializer_class = UserBankAccountSerializer
    permission_classes = [permissions.AllowAny]
