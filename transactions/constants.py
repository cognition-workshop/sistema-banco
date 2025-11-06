DEPOSIT = 1
WITHDRAWAL = 2
INTEREST = 3
PIX_SENT = 4
PIX_RECEIVED = 5

TRANSACTION_TYPE_CHOICES = (
    (DEPOSIT, 'Deposit'),
    (WITHDRAWAL, 'Withdrawal'),
    (INTEREST, 'Interest'),
    (PIX_SENT, 'PIX Enviado'),
    (PIX_RECEIVED, 'PIX Recebido'),
)
