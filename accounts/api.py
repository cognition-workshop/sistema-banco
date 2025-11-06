from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import BasePermission
from rest_framework.exceptions import NotAuthenticated
from rest_framework import status

from .serializers import AccountBalanceSerializer


class IsAuthenticatedWithProperStatus(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            raise NotAuthenticated('Authentication credentials were not provided.')
        return True


class AccountBalanceAPIView(APIView):
    permission_classes = [IsAuthenticatedWithProperStatus]
    
    def get(self, request):
        user = request.user
        
        if not hasattr(user, 'account'):
            return Response(
                {'detail': 'Account not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = AccountBalanceSerializer(user.account)
        return Response(serializer.data)
