DEPOSIT = 1
WITHDRAWAL = 2
INTEREST = 3
PIX = 4

TRANSACTION_TYPE_CHOICES = (
    (DEPOSIT, 'Deposit'),
    (WITHDRAWAL, 'Withdrawal'),
    (INTEREST, 'Interest'),
    (PIX, 'PIX'),
)

CPF_KEY = 'CPF'
EMAIL_KEY = 'EMAIL'
PHONE_KEY = 'PHONE'
RANDOM_KEY = 'RANDOM'

PIX_KEY_TYPE_CHOICES = (
    (CPF_KEY, 'CPF'),
    (EMAIL_KEY, 'Email'),
    (PHONE_KEY, 'Telefone'),
    (RANDOM_KEY, 'Chave Aleatória'),
)

PIX_PENDING = 'PENDING'
PIX_COMPLETED = 'COMPLETED'
PIX_FAILED = 'FAILED'
PIX_CANCELLED = 'CANCELLED'

PIX_STATUS_CHOICES = (
    (PIX_PENDING, 'Pendente'),
    (PIX_COMPLETED, 'Concluída'),
    (PIX_FAILED, 'Falhou'),
    (PIX_CANCELLED, 'Cancelada'),
)
