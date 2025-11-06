from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import NotFound
from .models import UserBankAccount
from .serializers import UserBankAccountSerializer


class AccountBalanceAPIView(generics.RetrieveAPIView):
    serializer_class = UserBankAccountSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        try:
            return self.request.user.account
        except UserBankAccount.DoesNotExist:
            raise NotFound(detail="User has no associated bank account")

    def get_queryset(self):
        return UserBankAccount.objects.filter(user=self.request.user)
