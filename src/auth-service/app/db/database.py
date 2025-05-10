import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.utils.logger import DefaultLogger
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/auth_db")

logger = DefaultLogger.get_logger()

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
SQLAlchemyInstrumentor().instrument(
    engine=engine
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()