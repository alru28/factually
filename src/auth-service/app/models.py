from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List


class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    is_active: bool
    is_verified: bool
    created_at: datetime

    class Config:
        orm_mode = True


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class APIKeyResponse(BaseModel):
    id: int
    key: str
    created_at: datetime
    expires_at: Optional[datetime]

    class Config:
        orm_mode = True

class APIKeyListResponse(BaseModel):
    api_keys: List[APIKeyResponse]


class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

class MessageResponse(BaseModel):
    message: str


class VerifyEmailRequest(BaseModel):
    token: str
