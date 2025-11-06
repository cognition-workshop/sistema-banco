from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from .models import UserBankAccount
from .serializers import UserBankAccountSerializer


class AccountBalanceDetailView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, account_no):
        try:
            account = UserBankAccount.objects.select_related('account_type').get(account_no=account_no)
        except UserBankAccount.DoesNotExist:
            return Response(
                {'error': 'Account not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if account.user != request.user:
            return Response(
                {'error': 'You do not have permission to access this account'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = UserBankAccountSerializer(account)
        return Response(serializer.data)
