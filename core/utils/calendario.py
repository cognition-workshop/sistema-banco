from datetime import datetime, timedelta
from ..models import FeriadoBancario


def eh_dia_util(data):
    """Check if date is a business day (not weekend or holiday)."""
    if isinstance(data, str):
        data = datetime.strptime(data, '%Y-%m-%d').date()
    
    if data.weekday() in [5, 6]:
        return False
    
    if FeriadoBancario.objects.filter(data=data).exists():
        return False
    
    if FeriadoBancario.objects.filter(
        data__month=data.month,
        data__day=data.day,
        recorrente=True
    ).exists():
        return False
    
    return True


def proximo_dia_util(data):
    """Get next business day."""
    if isinstance(data, str):
        data = datetime.strptime(data, '%Y-%m-%d').date()
    
    proxima_data = data + timedelta(days=1)
    while not eh_dia_util(proxima_data):
        proxima_data += timedelta(days=1)
    
    return proxima_data


def dias_uteis_entre(data_inicio, data_fim):
    """Count business days between two dates."""
    if isinstance(data_inicio, str):
        data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
    if isinstance(data_fim, str):
        data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
    
    dias_uteis = 0
    data_atual = data_inicio
    
    while data_atual <= data_fim:
        if eh_dia_util(data_atual):
            dias_uteis += 1
        data_atual += timedelta(days=1)
    
    return dias_uteis
