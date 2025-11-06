from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import UserBankAccount
from .serializers import UserBankAccountSerializer


@api_view(['GET'])
def account_balance_view(request, account_no):
    if not request.user.is_authenticated:
        return Response(
            {'detail': 'Authentication credentials were not provided.'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    account = get_object_or_404(UserBankAccount, account_no=account_no)
    
    if account.user != request.user:
        return Response(
            {'error': 'You do not have permission to access this account.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    serializer = UserBankAccountSerializer(account)
    return Response(serializer.data)
