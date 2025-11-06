from sqlalchemy import Column, Integer, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Transaction(Base):
    __tablename__ = "transactions_transaction"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts_userbankaccount.id"))
    amount = Column(Numeric(12, 2))
    balance_after_transaction = Column(Numeric(12, 2))
    transaction_type = Column(Integer)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    account = relationship("UserBankAccount", back_populates="transactions")
