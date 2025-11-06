DEPOSIT = 1
WITHDRAWAL = 2
INTEREST = 3

TRANSACTION_TYPE_CHOICES = (
    (DEPOSIT, 'Deposit'),
    (WITHDRAWAL, 'Withdrawal'),
    (INTEREST, 'Interest'),
)

AUDIT_DEPOSIT = 'deposit'
AUDIT_WITHDRAWAL = 'withdrawal'
AUDIT_INTEREST = 'interest'
AUDIT_BALANCE_ADJUSTMENT = 'balance_adjustment'
