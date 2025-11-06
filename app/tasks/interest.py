from datetime import datetime
from app.database import SessionLocal
from app.models.account import UserBankAccount
from app.models.transaction import Transaction
from app.tasks.celery_app import app


@app.task(name="app.tasks.interest.calculate_interest")
def calculate_interest():
    db = SessionLocal()
    try:
        accounts = db.query(UserBankAccount).filter(
            UserBankAccount.balance > 0,
            UserBankAccount.interest_start_date <= datetime.utcnow().date(),
            UserBankAccount.initial_deposit_date.isnot(None)
        ).all()
        
        this_month = datetime.utcnow().month
        
        for account in accounts:
            if this_month in account.get_interest_calculation_months():
                interest = account.account_type.calculate_interest(account.balance)
                
                account.balance += interest
                
                transaction = Transaction(
                    account_id=account.id,
                    amount=interest,
                    balance_after_transaction=account.balance,
                    transaction_type=3
                )
                db.add(transaction)
        
        db.commit()
    finally:
        db.close()
