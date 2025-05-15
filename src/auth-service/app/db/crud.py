from sqlalchemy.orm import Session
from app.db.schema import User, APIKey
import datetime
from app.utils.security import hash_password, generate_token, generate_api_key
from app.models import UserCreate, UserResponse, LoginRequest, APIKeyResponse, PasswordResetRequest, PasswordResetConfirm

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, user: UserCreate):
    hashed_pw = hash_password(user.password)
    verification_token = generate_token()
    db_user = User(
        email=user.email,
        hashed_password=hashed_pw,
        email_verification_token=verification_token
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def create_api_key(db: Session, user_id: int):
    key = generate_api_key()
    expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=3)
    api_key = APIKey(key=key, user_id=user_id, expires_at=expires_at)
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    return api_key

def verify_email(db: Session, token: str):
    user = db.query(User).filter(User.email_verification_token == token).first()
    if user:
        user.is_verified = True
        user.email_verification_token = None
        db.commit()
    return user

def create_password_reset_token(db: Session, email: str):
    user = get_user_by_email(db, email)
    if user:
        token = generate_token()
        user.password_reset_token = token
        db.commit()
        db.refresh(user)
        return token
    return None

def reset_password(db: Session, token: str, new_password: str):
    user = db.query(User).filter(User.password_reset_token == token).first()
    if user:
        user.hashed_password = hash_password(new_password)
        user.password_reset_token = None
        db.commit()
        db.refresh(user)
        return user
    return None

def get_api_keys_for_user(db: Session, user_id: int):
    return db.query(APIKey).filter(APIKey.user_id == user_id).all()

def renew_api_key(db: Session, api_key_id: int, user_id: int):
    api_key = db.query(APIKey).filter(APIKey.id == api_key_id, APIKey.user_id == user_id).first()
    if api_key:
        api_key.expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=3)
        db.commit()
        db.refresh(api_key)
    return api_key

def revoke_api_key(db: Session, api_key_id: int, user_id: int):
    api_key = db.query(APIKey).filter(APIKey.id == api_key_id, APIKey.user_id == user_id).first()
    if api_key:
        db.delete(api_key)
        db.commit()
        return True
    return False