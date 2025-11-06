from sqlalchemy import Column, Integer, String, Numeric, Date, ForeignKey
from sqlalchemy.orm import relationship
from decimal import Decimal
from app.database import Base


class BankAccountType(Base):
    __tablename__ = "accounts_bankaccounttype"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128))
    maximum_withdrawal_amount = Column(Numeric(12, 2))
    annual_interest_rate = Column(Numeric(5, 2))
    interest_calculation_per_year = Column(Integer)
    
    accounts = relationship("UserBankAccount", back_populates="account_type")
    
    def calculate_interest(self, principal: Decimal) -> Decimal:
        """
        Calculate interest for each account type.
        
        This uses a basic interest calculation formula
        """
        p = principal
        r = self.annual_interest_rate
        n = Decimal(self.interest_calculation_per_year)
        
        interest = (p * (1 + ((r/100) / n))) - p
        
        return round(interest, 2)


class UserBankAccount(Base):
    __tablename__ = "accounts_userbankaccount"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("accounts_user.id"), unique=True)
    account_type_id = Column(Integer, ForeignKey("accounts_bankaccounttype.id"))
    account_no = Column(Integer, unique=True, index=True)
    gender = Column(String(1))
    birth_date = Column(Date, nullable=True)
    balance = Column(Numeric(12, 2), default=0)
    interest_start_date = Column(Date, nullable=True)
    initial_deposit_date = Column(Date, nullable=True)
    
    user = relationship("User", back_populates="account")
    account_type = relationship("BankAccountType", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account")
    
    def get_interest_calculation_months(self):
        """
        List of month numbers for which the interest will be calculated
        
        returns [2, 4, 6, 8, 10, 12] for every 2 months interval
        """
        if not self.interest_start_date:
            return []
        interval = int(12 / self.account_type.interest_calculation_per_year)
        start = self.interest_start_date.month
        return [i for i in range(start, 13, interval)]


class UserAddress(Base):
    __tablename__ = "accounts_useraddress"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("accounts_user.id"), unique=True)
    street_address = Column(String(512))
    city = Column(String(256))
    postal_code = Column(Integer)
    country = Column(String(256))
    
    user = relationship("User", back_populates="address")
