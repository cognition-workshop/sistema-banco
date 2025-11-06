DEPOSIT = 1
WITHDRAWAL = 2
INTEREST = 3
PIX_SENT = 4
PIX_RECEIVED = 5

TRANSACTION_TYPE_CHOICES = (
    (DEPOSIT, 'Deposit'),
    (WITHDRAWAL, 'Withdrawal'),
    (INTEREST, 'Interest'),
    (PIX_SENT, 'PIX Sent'),
    (PIX_RECEIVED, 'PIX Received'),
)

PIX_KEY_CPF = 'CPF'
PIX_KEY_EMAIL = 'EMAIL'
PIX_KEY_PHONE = 'PHONE'
PIX_KEY_RANDOM = 'RANDOM'

PIX_KEY_TYPE_CHOICES = (
    (PIX_KEY_CPF, 'CPF'),
    (PIX_KEY_EMAIL, 'E-mail'),
    (PIX_KEY_PHONE, 'Telefone'),
    (PIX_KEY_RANDOM, 'Chave Aleatória'),
)
