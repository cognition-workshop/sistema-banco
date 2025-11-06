from pydantic import BaseModel, EmailStr, Field
from datetime import date
from typing import Optional


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: str
    last_name: str
    account_type_id: int
    account_no: int
    gender: str = Field(..., pattern="^[MF]$")
    birth_date: Optional[date] = None
    street_address: str
    city: str
    postal_code: int
    country: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class UserResponse(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    
    class Config:
        from_attributes = True
