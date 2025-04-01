from fastapi import APIRouter, HTTPException, Depends
from app.utils.logger import DefaultLogger
from app.db.database import get_db
from app.models import UserCreate, UserResponse, LoginRequest, APIKeyResponse, PasswordResetRequest, PasswordResetConfirm
from app.db.schema import User, APIKey
from sqlalchemy.orm import Session
from app.db.crud import create_user, get_user_by_email, create_api_key, verify_email, create_password_reset_token, reset_password
from app.utils.security import verify_password
from app.utils.mail_helper import send_email
import datetime

logger = DefaultLogger("AuthService").get_logger()

router = APIRouter()

# Registration Endpoint
@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    if get_user_by_email(db, user.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    created_user = create_user(db, user)
    
    send_email(
        recipient=created_user.email,
        subject="Verify your email",
        body=f"Please verify your email using this token: {created_user.email_verification_token}"
    )

    return created_user

# Login Endpoint
# @router.post("/login")
# async def login(credentials: LoginRequest, db: Session = Depends(get_db)):
#     user = get_user_by_email(db, credentials.email)
#     if not user or not verify_password(credentials.password, user.hashed_password):
#         raise HTTPException(status_code=401, detail="Invalid credentials")
#     if not user.is_verified:
#         raise HTTPException(status_code=401, detail="Email not verified")
#     # Normally, generate and return a JWT token; here we return a simple message.
#     return {"message": "Login successful"}

# API Key Request Endpoint
@router.post("/apikeys", response_model=APIKeyResponse)
async def request_api_key(credentials: LoginRequest, db: Session = Depends(get_db)):
    user = get_user_by_email(db, credentials.email)
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    api_key = create_api_key(db, user.id)
    return api_key

# API Key Validation Endpoint
@router.get("/validate")
async def validate_api_key(key: str, db: Session = Depends(get_db)):
    api_key = db.query(APIKey).filter(APIKey.key == key).first()
    if not api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    if api_key.expires_at and api_key.expires_at < datetime.datetime.now(datetime.timezone.utc):
        raise HTTPException(status_code=401, detail="API key expired")
    return {"message": "API key is valid", "user_id": api_key.user_id}

# Password Reset Request Endpoint
@router.post("/password-reset/request")
async def password_reset_request(request: PasswordResetRequest, db: Session = Depends(get_db)):
    token = create_password_reset_token(db, request.email)
    if not token:
        raise HTTPException(status_code=404, detail="Email not found")
    
    send_email(
        recipient=request.email,
        subject="Password Reset Request",
        body=f"Use this token to reset your password: {token}"
    )

    return {"message": "Password reset token sent to email"}

# Password Reset Confirmation Endpoint
@router.post("/password-reset/confirm")
async def password_reset_confirm(reset: PasswordResetConfirm, db: Session = Depends(get_db)):
    user = reset_password(db, reset.token, reset.new_password)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid token")
    return {"message": "Password successfully reset"}

# Email Verification Endpoint
@router.get("/verify-email")
async def verify_email(token: str, db: Session = Depends(get_db)):
    user = verify_email(db, token)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid token")
    return {"message": "Email successfully verified"}