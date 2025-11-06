class BankingSystemException(Exception):
    """Base exception para o sistema bancário"""

    pass


class InsufficientBalanceException(BankingSystemException):
    """Exceção para saldo insuficiente"""

    pass


class InvalidTransactionException(BankingSystemException):
    """Exceção para transação inválida"""

    pass


class AccountNotFoundException(BankingSystemException):
    """Exceção para conta não encontrada"""

    pass


class ValidationException(BankingSystemException):
    """Exceção para erros de validação"""

    pass
