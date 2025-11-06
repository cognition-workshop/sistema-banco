from workalendar.america import Brazil

def is_business_day(date):
    """Verifica se é dia útil bancário"""
    cal = Brazil()
    return cal.is_working_day(date)

def next_business_day(date):
    """Retorna próximo dia útil"""
    cal = Brazil()
    return cal.find_following_working_day(date)
