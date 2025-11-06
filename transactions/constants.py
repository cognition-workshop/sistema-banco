DEPOSIT = 1
WITHDRAWAL = 2
INTEREST = 3
PIX_TRANSFER = 4

TRANSACTION_TYPE_CHOICES = (
    (DEPOSIT, 'Depósito'),
    (WITHDRAWAL, 'Saque'),
    (INTEREST, 'Juros'),
    (PIX_TRANSFER, 'Transferência PIX'),
)

PIX_KEY_TYPES = (
    ('CPF', 'CPF'),
    ('EMAIL', 'Email'),
    ('PHONE', 'Telefone'),
    ('RANDOM', 'Chave Aleatória'),
)
