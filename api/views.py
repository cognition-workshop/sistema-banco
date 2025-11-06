from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from accounts.models import UserBankAccount
from .serializers import AccountBalanceSerializer


class AccountBalanceView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='Get account balance',
        description='Returns the balance of the authenticated user\'s account. Users can only access their own account.',
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='Account ID',
                required=True,
            ),
        ],
        responses={
            200: AccountBalanceSerializer,
            403: {'description': 'Forbidden - trying to access another user\'s account'},
            404: {'description': 'Account not found'},
        },
        tags=['Accounts']
    )
    def get(self, request, id):
        account = get_object_or_404(UserBankAccount, account_no=id)
        
        if account.user != request.user:
            return Response(
                {'detail': 'You do not have permission to access this account.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = AccountBalanceSerializer(account)
        return Response(serializer.data, status=status.HTTP_200_OK)
