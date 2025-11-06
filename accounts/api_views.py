from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from accounts.models import UserBankAccount
from accounts.serializers import AccountBalanceSerializer


class AccountBalanceAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, account_no=None):
        if account_no:
            try:
                account = UserBankAccount.objects.get(account_no=account_no)
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
        else:
            if not hasattr(request.user, 'account'):
                return Response(
                    {'error': 'No account found for this user'},
                    status=status.HTTP_404_NOT_FOUND
                )
            account = request.user.account
        
        serializer = AccountBalanceSerializer(account)
        return Response(serializer.data, status=status.HTTP_200_OK)
