from fastapi import APIRouter, HTTPException, Depends, Header
from app.utils.logger import DefaultLogger
from app.db.database import get_db
from app.models import UserCreate, UserResponse, LoginRequest, APIKeyResponse, PasswordResetRequest, PasswordResetConfirm, VerifyEmailRequest, TokenResponse, APIKeyListResponse
from app.db.schema import User, APIKey
from sqlalchemy.orm import Session
from app.db.crud import create_user, get_user_by_email, create_api_key, verify_email, create_password_reset_token, reset_password, revoke_api_key, renew_api_key, get_api_keys_for_user
from app.utils.security import verify_password, create_jwt, get_current_user
from app.utils.mail_helper import send_email
import datetime

logger = DefaultLogger().get_logger()

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
@router.post("/login", response_model=TokenResponse)
async def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    logger.info(f"Received login request for user {credentials.email}")
    user = get_user_by_email(db, credentials.email)
    if not user or not verify_password(credentials.password, user.hashed_password):
        logger.error(f"Login failed for user {credentials.email}: Invalid credentials")
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_verified:
        logger.error(f"Login failed for user {credentials.email}: Email not verified")
        raise HTTPException(status_code=401, detail="Email not verified")
    logger.info(f"User {user.email} login successfully; generated JWT token")
    token = create_jwt(user.id)
    response = TokenResponse(access_token=token)
    return response

# API Key Request Endpoint
@router.post("/apikeys", response_model=APIKeyResponse)
async def request_api_key(credentials: LoginRequest, db: Session = Depends(get_db)):
    logger.info(f"Received API Key request for user {credentials.email}")
    user = get_user_by_email(db, credentials.email)
    if not user or not verify_password(credentials.password, user.hashed_password):
        logger.error(f"API Key request failed for user {credentials.email}: Invalid credentials")
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Email not verified")
    api_key = create_api_key(db, user.id)
    logger.info(f"API Key provisioned succesfully for user {credentials.email}")
    return api_key

# API Key Validation Endpoint
@router.get("/validate")
async def validate_api_key(x_api_key: str = Header(..., alias="X-API-Key"), db: Session = Depends(get_db)):
    logger.info("Received API key validation request")
    api_key = db.query(APIKey).filter(APIKey.key == x_api_key).first()
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

# List API keys
@router.get("/apikeys", response_model=APIKeyListResponse)
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logger.info("Received API key listing request")
    api_keys = get_api_keys_for_user(db, current_user.id)
    if not api_keys:
        logger.error(f"No API keys found for user ID {current_user.id}")
        raise HTTPException(status_code=404, detail="No API keys found")
    logger.info(f"API keys listed successfully for user ID {current_user.id}")
    response = []
    for key in api_keys:
        formatted_key = APIKeyResponse(
            id=key.id,
            key=key.key,
            created_at=key.created_at,
            expires_at=key.expires_at,
        )
        response.append(formatted_key)
    return APIKeyListResponse(api_keys=response)

# Renew API key
@router.post("/apikeys/{api_key_id}/renew", response_model=APIKeyResponse)
async def renew_key(
    api_key_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logger.info("Received API key renewal request")
    api_key = renew_api_key(db, api_key_id, current_user.id)
    if not api_key:
        logger.error(f"There's no such API Key for user ID {current_user.id}")
        raise HTTPException(status_code=404, detail="API key not found")
    logger.info("API key renewed successfully for user ID {api_key.user_id}")
    return api_key

# Revoke API key
@router.delete("/apikeys/{api_key_id}")
async def revoke_key(
    api_key_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logger.info("Received API key revoke request")
    if not revoke_api_key(db, api_key_id, current_user.id):
        logger.error(f"There's no such API Key for user ID {current_user.id} or it has already been revoked")
        raise HTTPException(status_code=404, detail="API key not found or already revoked")
    logger.info(f"API key revoked successfully for user ID {current_user.id}")
    return {"message": "API key revoked successfully"}

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
@router.post("/verify-email")
async def verify_email_request(request: VerifyEmailRequest, db: Session = Depends(get_db)):
    logger.info(f"Received Email Verification request")
    user = verify_email(db, request.token)
    if not user:
        logger.error(f"Email Verification request failed: Invalid token")
        raise HTTPException(status_code=400, detail="Invalid token")
    print(f"USER: {user}")
    logger.info(f"Email Verification successful for user {user.email}")
    return {"message": "Email successfully verified"}