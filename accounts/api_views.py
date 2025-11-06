from rest_framework import viewsets, generics, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import get_user_model
from .models import UserBankAccount, BankAccountType
from .serializers import (
    UserSerializer, UserBankAccountSerializer, 
    BankAccountTypeSerializer, UserRegistrationSerializer
)

User = get_user_model()


class BankAccountTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = BankAccountType.objects.all()
    serializer_class = BankAccountTypeSerializer
    permission_classes = [AllowAny]


class UserRegistrationAPIView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        from rest_framework.authtoken.models import Token
        token, created = Token.objects.get_or_create(user=user)
        
        return Response({
            'user': UserSerializer(user).data,
            'token': token.key,
            'message': f'Account created successfully. Account number: {user.account.account_no}'
        }, status=status.HTTP_201_CREATED)


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return User.objects.filter(id=self.request.user.id)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


class UserBankAccountViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UserBankAccountSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return UserBankAccount.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def my_account(self, request):
        try:
            account = request.user.account
            serializer = self.get_serializer(account)
            return Response(serializer.data)
        except UserBankAccount.DoesNotExist:
            return Response(
                {'error': 'No bank account found for this user'},
                status=status.HTTP_404_NOT_FOUND
            )
