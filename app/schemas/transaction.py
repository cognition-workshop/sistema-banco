from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import datetime
from typing import Optional


class TransactionCreate(BaseModel):
    amount: Decimal = Field(..., gt=0)
    transaction_type: int


class DepositRequest(BaseModel):
    amount: Decimal = Field(..., ge=10, description="Minimum deposit is $10")


class WithdrawRequest(BaseModel):
    amount: Decimal = Field(..., ge=10, description="Minimum withdrawal is $10")


class TransactionResponse(BaseModel):
    id: int
    amount: Decimal
    balance_after_transaction: Decimal
    transaction_type: int
    timestamp: datetime
    
    class Config:
        from_attributes = True


class TransactionReportQuery(BaseModel):
    date_from: Optional[str] = None
    date_to: Optional[str] = None
