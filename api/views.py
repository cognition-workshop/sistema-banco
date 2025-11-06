from rest_framework import viewsets
from django.contrib.auth import get_user_model
from accounts.models import UserBankAccount
from transactions.models import Transaction
from accounts.serializers import UserSerializer, BankAccountSerializer
from transactions.serializers import TransactionSerializer

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class BankAccountViewSet(viewsets.ModelViewSet):
    queryset = UserBankAccount.objects.all()
    serializer_class = BankAccountSerializer


class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
