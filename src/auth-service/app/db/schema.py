from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import engine
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    email_verification_token = Column(String, nullable=True)
    password_reset_token = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now(datetime.timezone.utc))
    updated_at = Column(DateTime, default=datetime.now(datetime.timezone.utc))

    api_keys = relationship("APIKey", back_populates="user")

class APIKey(Base):
    __tablename__ = "api_keys"
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.now(datetime.timezone.utc))
    expires_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="api_keys")
