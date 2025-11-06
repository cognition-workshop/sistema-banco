from pydantic import BaseModel
from decimal import Decimal
from datetime import date
from typing import Optional


class BankAccountTypeResponse(BaseModel):
    id: int
    name: str
    maximum_withdrawal_amount: Decimal
    annual_interest_rate: Decimal
    interest_calculation_per_year: int
    
    class Config:
        from_attributes = True


class UserBankAccountResponse(BaseModel):
    id: int
    account_no: int
    gender: str
    birth_date: Optional[date]
    balance: Decimal
    interest_start_date: Optional[date]
    initial_deposit_date: Optional[date]
    account_type: BankAccountTypeResponse
    
    class Config:
        from_attributes = True
