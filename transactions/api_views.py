from rest_framework import viewsets, generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Transaction
from .serializers import TransactionSerializer, DepositSerializer, WithdrawSerializer


class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Transaction.objects.filter(account__user=self.request.user)


class DepositAPIView(generics.CreateAPIView):
    serializer_class = DepositSerializer
    permission_classes = [IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        transaction = serializer.save()
        
        return Response({
            'transaction': TransactionSerializer(transaction).data,
            'message': f'{transaction.amount} deposited successfully'
        }, status=status.HTTP_201_CREATED)


class WithdrawAPIView(generics.CreateAPIView):
    serializer_class = WithdrawSerializer
    permission_classes = [IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        transaction = serializer.save()
        
        return Response({
            'transaction': TransactionSerializer(transaction).data,
            'message': f'{transaction.amount} withdrawn successfully'
        }, status=status.HTTP_201_CREATED)
