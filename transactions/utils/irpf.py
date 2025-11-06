from decimal import Decimal
from datetime import datetime
from django.db.models import Sum
from transactions.models import Transaction
from transactions.constants import INTEREST


def calcular_rendimentos_ano(user, ano):
    """Calculate annual income for IRPF."""
    start_date = datetime(ano, 1, 1)
    end_date = datetime(ano, 12, 31, 23, 59, 59)
    
    interest_transactions = Transaction.objects.filter(
        account__user=user,
        transaction_type=INTEREST,
        timestamp__gte=start_date,
        timestamp__lte=end_date
    )
    
    rendimentos_juros = interest_transactions.aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0.00')
    
    limite_isencao_mensal = Decimal('500.00')
    limite_isencao_anual = limite_isencao_mensal * 12
    
    rendimentos_isentos = min(rendimentos_juros, limite_isencao_anual)
    rendimentos_tributaveis = max(Decimal('0.00'), rendimentos_juros - limite_isencao_anual)
    
    return {
        'rendimentos_totais': rendimentos_juros,
        'rendimentos_isentos': rendimentos_isentos,
        'rendimentos_tributaveis': rendimentos_tributaveis,
        'transacoes': interest_transactions
    }
