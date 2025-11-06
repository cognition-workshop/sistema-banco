from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from app.database import get_db
from app.schemas.user import UserCreate, Token, UserResponse
from app.schemas.account import UserBankAccountResponse
from app.models.user import User
from app.models.account import UserBankAccount, UserAddress, BankAccountType
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.config import settings
from app.api.deps import get_current_user

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.post("/register/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    existing_account = db.query(UserBankAccount).filter(
        UserBankAccount.account_no == user_data.account_no
    ).first()
    if existing_account:
        raise HTTPException(status_code=400, detail="Account number already exists")
    
    account_type = db.query(BankAccountType).filter(
        BankAccountType.id == user_data.account_type_id
    ).first()
    if not account_type:
        raise HTTPException(status_code=400, detail="Invalid account type")
    
    user = User(
        email=user_data.email,
        password=get_password_hash(user_data.password),
        first_name=user_data.first_name,
        last_name=user_data.last_name
    )
    db.add(user)
    db.flush()
    
    account = UserBankAccount(
        user_id=user.id,
        account_type_id=user_data.account_type_id,
        account_no=user_data.account_no,
        gender=user_data.gender,
        birth_date=user_data.birth_date
    )
    db.add(account)
    
    address = UserAddress(
        user_id=user.id,
        street_address=user_data.street_address,
        city=user_data.city,
        postal_code=user_data.postal_code,
        country=user_data.country
    )
    db.add(address)
    
    db.commit()
    db.refresh(user)
    
    return user


@router.post("/login/", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout/")
def logout():
    return {"message": "Logout successful. Please delete the token on the client side."}


@router.get("/me/", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/me/account/", response_model=UserBankAccountResponse)
def get_current_user_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not hasattr(current_user, 'account') or current_user.account is None:
        raise HTTPException(status_code=404, detail="User does not have a bank account")
    
    return current_user.account
