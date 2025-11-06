from django.http import JsonResponse
from django.views import View
from django.contrib.auth import get_user_model


class BalanceAPIView(View):
    def get(self, request):
        User = get_user_model()
        demo_user = User.objects.filter(email='demo@example.com').first()
        
        if demo_user and hasattr(demo_user, 'account'):
            balance = demo_user.account.balance
            return JsonResponse({
                'balance': float(balance),
                'formatted': f'R$ {balance:.2f}'
            })
        
        return JsonResponse({'balance': 0, 'formatted': 'R$ 0.00'})


class ValidateAmountAPIView(View):
    def get(self, request):
        amount_str = request.GET.get('amount', '0')
        try:
            amount = float(amount_str.replace('R$', '').replace('.', '').replace(',', '.').strip())
            
            if amount <= 0:
                return JsonResponse({
                    'valid': False,
                    'message': 'O valor deve ser maior que zero'
                })
            
            if amount < 100:
                return JsonResponse({
                    'valid': False,
                    'message': 'O valor mínimo é R$ 100,00'
                })
            
            return JsonResponse({
                'valid': True,
                'message': 'Valor válido'
            })
        except (ValueError, AttributeError):
            return JsonResponse({
                'valid': False,
                'message': 'Valor inválido'
            })
