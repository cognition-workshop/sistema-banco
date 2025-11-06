from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import User, BankAccountType, UserBankAccount, UserAddress
from .serializers import (
    UserSerializer, BankAccountTypeSerializer, 
    UserBankAccountSerializer, UserAddressSerializer
)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]


class BankAccountTypeViewSet(viewsets.ModelViewSet):
    queryset = BankAccountType.objects.all()
    serializer_class = BankAccountTypeSerializer
    permission_classes = [IsAuthenticated]


class UserBankAccountViewSet(viewsets.ModelViewSet):
    queryset = UserBankAccount.objects.all()
    serializer_class = UserBankAccountSerializer
    permission_classes = [IsAuthenticated]


class UserAddressViewSet(viewsets.ModelViewSet):
    queryset = UserAddress.objects.all()
    serializer_class = UserAddressSerializer
    permission_classes = [IsAuthenticated]
