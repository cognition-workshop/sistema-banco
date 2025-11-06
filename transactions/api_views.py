from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction as db_transaction
from .models import Transaction
from .serializers import TransactionSerializer, TransactionCreateSerializer
from accounts.models import UserBankAccount
from .constants import DEPOSIT, WITHDRAWAL


class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Transaction.objects.select_related('account', 'account__user')
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return Transaction.objects.all()
        return Transaction.objects.filter(account__user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def deposit(self, request):
        serializer = TransactionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        amount = serializer.validated_data['amount']
        
        try:
            account = UserBankAccount.objects.get(user=request.user)
        except UserBankAccount.DoesNotExist:
            return Response(
                {'error': 'Conta bancária não encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        with db_transaction.atomic():
            account.balance += amount
            account.save(update_fields=['balance'])
            
            transaction_obj = Transaction.objects.create(
                account=account,
                amount=amount,
                balance_after_transaction=account.balance,
                transaction_type=DEPOSIT
            )
        
        return Response(
            TransactionSerializer(transaction_obj).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=False, methods=['post'])
    def withdraw(self, request):
        serializer = TransactionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        amount = serializer.validated_data['amount']
        
        try:
            account = UserBankAccount.objects.get(user=request.user)
        except UserBankAccount.DoesNotExist:
            return Response(
                {'error': 'Conta bancária não encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if amount > account.balance:
            return Response(
                {
                    'error': 'Saldo insuficiente',
                    'balance': float(account.balance),
                    'requested': float(amount)
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        max_withdrawal = account.account_type.maximum_withdrawal_amount
        if amount > max_withdrawal:
            return Response(
                {
                    'error': f'Valor máximo de saque: R$ {max_withdrawal}',
                    'maximum': float(max_withdrawal)
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with db_transaction.atomic():
            account.balance -= amount
            account.save(update_fields=['balance'])
            
            transaction_obj = Transaction.objects.create(
                account=account,
                amount=amount,
                balance_after_transaction=account.balance,
                transaction_type=WITHDRAWAL
            )
        
        return Response(
            TransactionSerializer(transaction_obj).data,
            status=status.HTTP_201_CREATED
        )
