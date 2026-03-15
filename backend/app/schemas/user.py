from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    user_login: str
    user_email: str
    user_nicename: str = ""
    display_name: str = ""
    user_url: str = ""


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    user_email: Optional[str] = None
    display_name: Optional[str] = None
    user_url: Optional[str] = None
    password: Optional[str] = None


class UserOut(UserBase):
    ID: int
    user_registered: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class LoginRequest(BaseModel):
    username: str
    password: str
