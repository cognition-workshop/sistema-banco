from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from decimal import Decimal
from datetime import datetime
from dateutil.relativedelta import relativedelta
from typing import Optional
from app.database import get_db
from app.schemas.transaction import DepositRequest, WithdrawRequest, TransactionResponse
from app.models.user import User
from app.models.transaction import Transaction
from app.api.deps import get_current_user

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("/deposit/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def deposit_money(
    deposit: DepositRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not hasattr(current_user, 'account') or current_user.account is None:
        raise HTTPException(status_code=400, detail="User does not have a bank account")
    
    account = current_user.account
    
    if not account.initial_deposit_date:
        now = datetime.utcnow()
        next_interest_month = int(
            12 / account.account_type.interest_calculation_per_year
        )
        account.initial_deposit_date = now.date()
        account.interest_start_date = (
            now + relativedelta(months=+next_interest_month)
        ).date()
    
    account.balance += deposit.amount
    
    transaction = Transaction(
        account_id=account.id,
        amount=deposit.amount,
        balance_after_transaction=account.balance,
        transaction_type=1
    )
    
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    
    return transaction


@router.post("/withdraw/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def withdraw_money(
    withdraw: WithdrawRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not hasattr(current_user, 'account') or current_user.account is None:
        raise HTTPException(status_code=400, detail="User does not have a bank account")
    
    account = current_user.account
    
    if withdraw.amount > account.account_type.maximum_withdrawal_amount:
        raise HTTPException(
            status_code=400,
            detail=f"You can withdraw at most ${account.account_type.maximum_withdrawal_amount}"
        )
    
    if withdraw.amount > account.balance:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient balance. Current balance: ${account.balance}"
        )
    
    account.balance -= withdraw.amount
    
    transaction = Transaction(
        account_id=account.id,
        amount=withdraw.amount,
        balance_after_transaction=account.balance,
        transaction_type=2
    )
    
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    
    return transaction


@router.get("/report/")
def transaction_report(
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not hasattr(current_user, 'account') or current_user.account is None:
        raise HTTPException(status_code=400, detail="User does not have a bank account")
    
    account = current_user.account
    
    query = db.query(Transaction).filter(Transaction.account_id == account.id)
    
    if date_from and date_to:
        try:
            start_date = datetime.strptime(date_from, "%Y-%m-%d")
            end_date = datetime.strptime(date_to, "%Y-%m-%d")
            query = query.filter(
                Transaction.timestamp >= start_date,
                Transaction.timestamp <= end_date
            )
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    transactions = query.order_by(Transaction.timestamp).all()
    
    transaction_list = []
    for t in transactions:
        transaction_list.append({
            "id": t.id,
            "transaction_type": {1: "Deposit", 2: "Withdrawal", 3: "Interest"}.get(t.transaction_type),
            "amount": float(t.amount),
            "balance_after_transaction": float(t.balance_after_transaction),
            "timestamp": t.timestamp.isoformat()
        })
    
    return {
        "account_number": account.account_no,
        "current_balance": float(account.balance),
        "transactions": transaction_list
    }
