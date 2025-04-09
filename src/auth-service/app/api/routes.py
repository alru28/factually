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
    logger.info(f"Received registration request for user {user.email}")
    if get_user_by_email(db, user.email):
        logger.error(f"Registration failed for user {user.email}: Email already exists")
        raise HTTPException(status_code=400, detail="Email already registered")
    try:
        created_user = create_user(db, user)
        send_email(
            recipient=created_user.email,
            subject="Verify your email",
            body=f"Please verify your email using this token: {created_user.email_verification_token}"
        )
        logger.info(f"User {user.email} registered successfully; verification email sent")
    except Exception as e:
        logger.error(f"Registration failed for user {user.email}: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")
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
    logger.info(f"Received API Key request for user {credentials.email}")
    user = get_user_by_email(db, credentials.email)
    if not user or not verify_password(credentials.password, user.hashed_password):
        logger.error(f"API Key request failed for user {credentials.email}: Invalid credentials")
        raise HTTPException(status_code=401, detail="Invalid credentials")
    api_key = create_api_key(db, user.id)
    logger.info(f"API Key provisioned succesfully for user {credentials.email}")
    return api_key

# API Key Validation Endpoint
@router.get("/validate")
async def validate_api_key(key: str, db: Session = Depends(get_db)):
    logger.info("Received API key validation request")
    api_key = db.query(APIKey).filter(APIKey.key == key).first()
    if not api_key:
        logger.error("API Key validation failed: Invalid API key")
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    now = datetime.datetime.now(datetime.timezone.utc)
    expires_at = api_key.expires_at
    if expires_at and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=datetime.timezone.utc)
    
    if expires_at and expires_at < now:
        logger.error("API Key validation failed: API key expired")
        raise HTTPException(status_code=401, detail="API key expired")
    
    logger.info(f"API key validated successfully for user ID {api_key.user_id}")
    return {"message": "API key is valid", "user_id": api_key.user_id}

# Password Reset Request Endpoint
@router.post("/password-reset/request")
async def password_reset_request(request: PasswordResetRequest, db: Session = Depends(get_db)):
    logger.info(f"Received Password Reset request for user {request.email}")
    token = create_password_reset_token(db, request.email)
    if not token:
        logger.error(f"Password Reset request failed for user {request.email}: Email not found")
        raise HTTPException(status_code=404, detail="Email not found")
    
    send_email(
        recipient=request.email,
        subject="Password Reset Request",
        body=f"Use this token to reset your password: {token}"
    )

    logger.info(f"Password Reset requested successfully for user {request.email}; reset email sent")
    return {"message": "Password reset token sent to email"}

# Password Reset Confirmation Endpoint
@router.post("/password-reset/confirm")
async def password_reset_confirm(reset: PasswordResetConfirm, db: Session = Depends(get_db)):
    logger.info(f"Received Password Confirmation request")
    user = reset_password(db, reset.token, reset.new_password)
    if not user:
        logger.error(f"Password Reset Confirmation failed: Invalid token")
        raise HTTPException(status_code=400, detail="Invalid token")
    logger.info(f"Password Reset Confirmation successful for user {user.email}")    
    return {"message": "Password successfully reset"}

# Email Verification Endpoint
@router.get("/verify-email")
async def verify_email(token: str, db: Session = Depends(get_db)):
    logger.info(f"Received Email Verification request")
    user = verify_email(db, token)
    if not user:
        logger.error(f"Email Verification request failed: Invalid token")
        raise HTTPException(status_code=400, detail="Invalid token")
    logger.info(f"Email Verification successful for user {user.email}")
    return {"message": "Email successfully verified"}