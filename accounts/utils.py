import datetime
from dateutil.relativedelta import relativedelta


def calculate_check_digit_modulo11(number_str):
    weights = list(range(2, 10)) + [2, 3, 4, 5, 6, 7, 8, 9]
    sum_val = 0
    for i, digit in enumerate(reversed(number_str)):
        sum_val += int(digit) * weights[i % len(weights)]
    
    remainder = sum_val % 11
    if remainder == 0 or remainder == 1:
        return 0
    return 11 - remainder


def validate_brazilian_account(agencia, conta):
    agencia_digito = calculate_check_digit_modulo11(str(agencia))
    conta_digito = calculate_check_digit_modulo11(str(conta))
    return agencia_digito, conta_digito


def format_account_number(agencia, agencia_digito, conta, conta_digito):
    return f'{agencia:04d}-{agencia_digito} {conta:08d}-{conta_digito}'


BRAZILIAN_BANKING_HOLIDAYS = {
    (1, 1): "Ano Novo",
    (4, 21): "Tiradentes",
    (5, 1): "Dia do Trabalho",
    (9, 7): "Independência do Brasil",
    (10, 12): "Nossa Senhora Aparecida",
    (11, 2): "Finados",
    (11, 15): "Proclamação da República",
    (11, 20): "Dia da Consciência Negra",
    (12, 25): "Natal",
}


def get_movable_holidays(year):
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    
    easter = datetime.date(year, month, day)
    
    return {
        easter - relativedelta(days=47): "Carnaval",
        easter - relativedelta(days=2): "Sexta-feira Santa",
        easter + relativedelta(days=60): "Corpus Christi",
    }


def is_banking_day(date):
    if date.weekday() >= 5:
        return False
    
    if (date.month, date.day) in BRAZILIAN_BANKING_HOLIDAYS:
        return False
    
    movable = get_movable_holidays(date.year)
    if date in movable:
        return False
    
    return True


def next_banking_day(date):
    next_day = date + relativedelta(days=1)
    while not is_banking_day(next_day):
        next_day += relativedelta(days=1)
    return next_day
