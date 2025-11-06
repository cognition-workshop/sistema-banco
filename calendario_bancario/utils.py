from datetime import datetime, date
from .models import FeriadoBancario


def is_dia_util(data):
    """
    Check if a date is a business day (not weekend or holiday)
    """
    if isinstance(data, datetime):
        data = data.date()
    
    if data.weekday() >= 5:
        return False
    
    return not FeriadoBancario.objects.filter(data=data, ativo=True).exists()


def calcular_feriados_moveis(ano):
    """
    Calculate movable holidays (Carnival, Good Friday, Corpus Christi)
    using dateutil for Easter calculation
    """
    from dateutil.easter import easter
    from datetime import timedelta
    
    pascoa = easter(ano)
    
    carnaval = pascoa - timedelta(days=47)
    sexta_feira_santa = pascoa - timedelta(days=2)
    corpus_christi = pascoa + timedelta(days=60)
    
    return [
        (carnaval, 'Carnaval'),
        (sexta_feira_santa, 'Sexta-feira Santa'),
        (corpus_christi, 'Corpus Christi'),
    ]
